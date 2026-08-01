from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from empresas.models import Loja, Matriz
from produtos.choices import OrigemPreco, StatusProduto
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)

from compras.choices import (
    StatusFornecedor,
    StatusPedidoCompra,
)
from compras.models import (
    Fornecedor,
    ItemPedidoCompra,
    PedidoCompra,
    RecebimentoCompra,
)
from compras.services import receber_pedido_compra


Usuario = get_user_model()


class CustosCompraServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Custos'
        )
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Custos',
        )
        self.usuario = Usuario.objects.create_user(
            username='usuario_custos',
            password='senha-segura',
            matriz=self.matriz,
        )
        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Custos LTDA',
            cnpj='33444555000102',
            status=StatusFornecedor.ATIVO,
        )
        self.categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Categoria Custos',
        )
        self.marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Marca Custos',
            fabricante='Fabricante Custos',
        )
        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )

        self.produto_a = self.criar_produto(
            codigo='CUS-001',
            sku='CUS-SKU-001',
            gtin='7891234567801',
            nome='Produto A',
        )
        self.produto_b = self.criar_produto(
            codigo='CUS-002',
            sku='CUS-SKU-002',
            gtin='7891234567802',
            nome='Produto B',
        )

        self.pedido = PedidoCompra.objects.create(
            matriz=self.matriz,
            fornecedor=self.fornecedor,
            numero=1,
            status=StatusPedidoCompra.ENVIADO,
            data_emissao=timezone.localdate(),
            frete=Decimal('30.00'),
            desconto=Decimal('10.00'),
            criado_por=self.usuario,
        )

        self.item_a = ItemPedidoCompra.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade=Decimal('10.000'),
            valor_unitario=Decimal('10.00'),
        )
        self.item_b = ItemPedidoCompra.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade=Decimal('10.000'),
            valor_unitario=Decimal('20.00'),
        )

    def criar_produto(self, *, codigo, sku, gtin, nome):
        return Produto.objects.create(
            matriz=self.matriz,
            categoria=self.categoria,
            marca=self.marca,
            unidade_medida=self.unidade,
            codigo_interno=codigo,
            sku=sku,
            gtin=gtin,
            ncm='21069030',
            nome=nome,
            custo_base=Decimal('1.00'),
            preco_venda=Decimal('30.00'),
            origem_preco=OrigemPreco.MANUAL,
            peso_liquido_gramas=100,
            peso_bruto_gramas=120,
            controla_estoque=True,
            estoque_minimo=Decimal('1.000'),
            status=StatusProduto.ATIVO,
        )

    def receber(self, *, itens, chave):
        return receber_pedido_compra(
            pedido=self.pedido,
            loja=self.loja,
            itens=itens,
            chave_idempotencia=chave,
            usuario=self.usuario,
        )

    def test_rateia_frete_e_desconto_por_valor(self):
        self.receber(
            itens=[
                {
                    'item_pedido_id': self.item_a.pk,
                    'quantidade': Decimal('10.000'),
                },
                {
                    'item_pedido_id': self.item_b.pk,
                    'quantidade': Decimal('10.000'),
                },
            ],
            chave='custos-rateio-1',
        )

        self.produto_a.refresh_from_db()
        self.produto_b.refresh_from_db()

        self.assertEqual(
            self.produto_a.custo_base,
            Decimal('10.67'),
        )
        self.assertEqual(
            self.produto_b.custo_base,
            Decimal('21.33'),
        )

    def test_recebimento_parcial_usa_custo_do_pedido_completo(self):
        self.receber(
            itens=[
                {
                    'item_pedido_id': self.item_a.pk,
                    'quantidade': Decimal('4.000'),
                },
            ],
            chave='custos-parcial-1',
        )

        self.produto_a.refresh_from_db()
        self.produto_b.refresh_from_db()

        self.assertEqual(
            self.produto_a.custo_base,
            Decimal('10.67'),
        )
        self.assertEqual(
            self.produto_b.custo_base,
            Decimal('1.00'),
        )

    def test_idempotencia_nao_reaplica_custo(self):
        itens = [{
            'item_pedido_id': self.item_a.pk,
            'quantidade': Decimal('4.000'),
        }]

        primeiro = self.receber(
            itens=itens,
            chave='custos-idempotencia-1',
        )

        self.produto_a.custo_base = Decimal('99.00')
        self.produto_a.save(
            update_fields=['custo_base', 'atualizado_em']
        )

        segundo = self.receber(
            itens=itens,
            chave='custos-idempotencia-1',
        )

        self.produto_a.refresh_from_db()

        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(
            self.produto_a.custo_base,
            Decimal('99.00'),
        )
        self.assertEqual(
            RecebimentoCompra.objects.count(),
            1,
        )

    def test_registra_auditoria_da_atualizacao(self):
        self.receber(
            itens=[{
                'item_pedido_id': self.item_a.pk,
                'quantidade': Decimal('2.000'),
            }],
            chave='custos-auditoria-1',
        )

        auditoria = RegistroAuditoria.objects.get(
            recurso='produtos.produto',
            recurso_id=str(self.produto_a.uuid),
            acao=RegistroAuditoria.ACAO_EDITAR,
        )

        self.assertEqual(auditoria.matriz, self.matriz)
        self.assertEqual(auditoria.loja, self.loja)
        self.assertIn(
            'custo_novo=10.67',
            auditoria.descricao,
        )

    def test_falha_na_auditoria_desfaz_recebimento_e_custo(self):
        with patch(
            'compras.services.custos.registrar_auditoria',
            side_effect=RuntimeError(
                'Falha simulada de auditoria'
            ),
        ):
            with self.assertRaises(RuntimeError):
                self.receber(
                    itens=[{
                        'item_pedido_id': self.item_a.pk,
                        'quantidade': Decimal('2.000'),
                    }],
                    chave='custos-rollback-1',
                )

        self.produto_a.refresh_from_db()

        self.assertEqual(
            self.produto_a.custo_base,
            Decimal('1.00'),
        )
        self.assertFalse(
            RecebimentoCompra.objects.exists()
        )

    def test_rateia_por_quantidade_quando_subtotal_e_zero(self):
        self.item_a.valor_unitario = Decimal('0.00')
        self.item_a.save(
            update_fields=[
                'valor_unitario',
                'atualizado_em',
            ]
        )
        self.item_b.valor_unitario = Decimal('0.00')
        self.item_b.save(
            update_fields=[
                'valor_unitario',
                'atualizado_em',
            ]
        )

        self.pedido.frete = Decimal('20.00')
        self.pedido.desconto = Decimal('0.00')
        self.pedido.save(
            update_fields=[
                'frete',
                'desconto',
                'atualizado_em',
            ]
        )

        self.receber(
            itens=[
                {
                    'item_pedido_id': self.item_a.pk,
                    'quantidade': Decimal('10.000'),
                },
                {
                    'item_pedido_id': self.item_b.pk,
                    'quantidade': Decimal('10.000'),
                },
            ],
            chave='custos-zero-1',
        )

        self.produto_a.refresh_from_db()
        self.produto_b.refresh_from_db()

        self.assertEqual(
            self.produto_a.custo_base,
            Decimal('1.00'),
        )
        self.assertEqual(
            self.produto_b.custo_base,
            Decimal('1.00'),
        )