
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
    DevolucaoCompra,
    Fornecedor,
    ItemPedidoCompra,
    PedidoCompra,
)
from compras.services import (
    devolver_recebimento_compra,
    receber_pedido_compra,
)


Usuario = get_user_model()


class DevolucaoCompraServicesTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Devolucao'
        )
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Devolucao',
        )
        self.usuario = Usuario.objects.create_user(
            username='usuario_devolucao',
            password='senha-segura',
            matriz=self.matriz,
        )
        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social='Fornecedor Devolucao LTDA',
            cnpj='22333444000191',
            status=StatusFornecedor.ATIVO,
        )
        categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Categoria Devolucao',
        )
        marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Marca Devolucao',
            fabricante='Fabricante Devolucao',
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
            codigo_interno='DEV-001',
            sku='DEV-SKU-001',
            gtin='7891234567891',
            ncm='21069030',
            nome='Produto Devolucao',
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
        self.item_pedido = ItemPedidoCompra.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade=Decimal('10.000'),
            valor_unitario=Decimal('10.00'),
        )
        self.recebimento = receber_pedido_compra(
            pedido=self.pedido,
            loja=self.loja,
            itens=[{
                'item_pedido_id': self.item_pedido.pk,
                'quantidade': Decimal('10.000'),
            }],
            chave_idempotencia='recebimento-base-devolucao',
            usuario=self.usuario,
        )
        self.item_recebimento = self.recebimento.itens.get()

    def devolver(self, quantidade, chave):
        return devolver_recebimento_compra(
            recebimento=self.recebimento,
            itens=[{
                'item_recebimento_id': self.item_recebimento.pk,
                'quantidade': quantidade,
            }],
            chave_idempotencia=chave,
            usuario=self.usuario,
            motivo='Produto avariado.',
        )

    def test_devolucao_parcial_reduz_estoque(self):
        self.devolver(
            Decimal('4.000'),
            'devolucao-parcial-1',
        )
        self.item_recebimento.refresh_from_db()

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            self.item_recebimento.quantidade_devolvida,
            Decimal('4.000'),
        )
        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('6.000'),
        )

    def test_devolucao_total_zera_estoque(self):
        self.devolver(
            Decimal('10.000'),
            'devolucao-total-1',
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('0.000'),
        )

    def test_impede_devolver_acima_do_recebido(self):
        with self.assertRaises(ValidationError):
            self.devolver(
                Decimal('11.000'),
                'devolucao-excedente-1',
            )

        self.assertFalse(
            DevolucaoCompra.objects.exists()
        )

    def test_idempotencia_nao_duplica_saida(self):
        primeira = self.devolver(
            Decimal('4.000'),
            'devolucao-idempotente-1',
        )
        segunda = self.devolver(
            Decimal('4.000'),
            'devolucao-idempotente-1',
        )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('6.000'),
        )
        self.assertEqual(
            DevolucaoCompra.objects.count(),
            1,
        )

    def test_impede_acumulado_acima_do_recebido(self):
        self.devolver(
            Decimal('7.000'),
            'devolucao-acumulada-1',
        )

        with self.assertRaises(ValidationError):
            self.devolver(
                Decimal('4.000'),
                'devolucao-acumulada-2',
            )

        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
        )

        self.assertEqual(
            saldo.quantidade_atual,
            Decimal('3.000'),
        )
