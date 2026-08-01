from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from empresas.models import Loja, Matriz
from estoque.models import SaldoEstoque
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


class RecebimentoCompraServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Recebimento'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Recebimento',
        )

        self.usuario = Usuario.objects.create_user(
            username='usuario_recebimento',
            password='senha-segura',
            matriz=self.matriz,
        )

        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Recebimento LTDA',
            cnpj='11222333000181',
            status=StatusFornecedor.ATIVO,
        )

        categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Categoria Recebimento',
        )

        marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Marca Recebimento',
            fabricante='Fabricante Recebimento',
        )

        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            categoria=categoria,
            marca=marca,
            unidade_medida=unidade,
            codigo_interno='REC-001',
            sku='REC-SKU-001',
            gtin='7891234567890',
            ncm='21069030',
            nome='Produto Recebimento',
            custo_base=Decimal('10.00'),
            preco_venda=Decimal('20.00'),
            origem_preco=OrigemPreco.MANUAL,
            peso_liquido_gramas=100,
            peso_bruto_gramas=120,
            controla_estoque=True,
            estoque_minimo=Decimal('1.000'),
            status=StatusProduto.ATIVO,
        )

        self.pedido = PedidoCompra.objects.create(
            matriz=self.matriz,
            fornecedor=self.fornecedor,
            numero=1,
            status=StatusPedidoCompra.ENVIADO,
            data_emissao=timezone.localdate(),
            criado_por=self.usuario,
        )

        self.item = ItemPedidoCompra.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade=Decimal('10.000'),
            valor_unitario=Decimal('10.00'),
        )

    def receber(self, quantidade, chave):
        return receber_pedido_compra(
            pedido=self.pedido,
            loja=self.loja,
            itens=[
                {
                    'item_pedido_id': self.item.pk,
                    'quantidade': quantidade,
                }
            ],
            chave_idempotencia=chave,
            usuario=self.usuario,
        )

    def test_recebimento_parcial_atualiza_estoque(self):
        self.receber(
            Decimal('4.000'),
            'recebimento-parcial-1',
        )

        self.item.refresh_from_db()
        self.pedido.refresh_from_db()

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            self.item.quantidade_recebida,
            Decimal('4.000'),
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('4.000'),
        )

        self.assertEqual(
            self.pedido.status,
            StatusPedidoCompra.PARCIAL,
        )

    def test_recebimento_total_finaliza_pedido(self):
        self.receber(
            Decimal('10.000'),
            'recebimento-total-1',
        )

        self.pedido.refresh_from_db()

        self.assertEqual(
            self.pedido.status,
            StatusPedidoCompra.RECEBIDO,
        )

    def test_impede_receber_acima_do_pendente(self):
        with self.assertRaises(ValidationError):
            self.receber(
                Decimal('11.000'),
                'recebimento-excedente-1',
            )

        self.assertFalse(
            RecebimentoCompra.objects.exists()
        )

    def test_idempotencia_nao_duplica_estoque(self):
        primeiro = self.receber(
            Decimal('4.000'),
            'recebimento-idempotente-1',
        )

        segundo = self.receber(
            Decimal('4.000'),
            'recebimento-idempotente-1',
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            primeiro.pk,
            segundo.pk,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('4.000'),
        )