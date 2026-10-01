from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from empresas.models import Loja, Matriz
from produtos.choices import OrigemPreco, StatusProduto
from produtos.models import Categoria, Marca, Produto, UnidadeMedida

from compras.choices import StatusFornecedor, StatusPedidoCompra
from compras.models import Fornecedor, ItemPedidoCompra, PedidoCompra
from compras.services.recebimentos import receber_pedido_compra
from financeiro.models import TituloFinanceiro


Usuario = get_user_model()


class F2BContasPagarRecebimentoRedTests(TestCase):
    """Contrato RED: recebimento deve originar obrigacao financeira estruturada."""

    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F2B RED")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja F2B RED",
        )
        self.usuario = Usuario.objects.create_user(
            username="usuario_f2b_red",
            password="senha-segura",
            matriz=self.matriz,
        )
        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social="Fornecedor F2B RED LTDA",
            cnpj="99888777000166",
            status=StatusFornecedor.ATIVO,
        )
        categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome="Categoria F2B RED",
        )
        marca = Marca.objects.create(
            matriz=self.matriz,
            nome="Marca F2B RED",
            fabricante="Fabricante F2B RED",
        )
        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla="UN",
            descricao="Unidade",
        )
        self.produto = Produto.objects.create(
            matriz=self.matriz,
            categoria=categoria,
            marca=marca,
            unidade_medida=unidade,
            codigo_interno="F2B-RED-001",
            sku="F2B-RED-SKU-001",
            gtin="7899876543210",
            ncm="21069030",
            nome="Produto F2B RED",
            custo_base=Decimal("10.00"),
            preco_venda=Decimal("20.00"),
            origem_preco=OrigemPreco.MANUAL,
            peso_liquido_gramas=100,
            peso_bruto_gramas=120,
            controla_estoque=True,
            estoque_minimo=Decimal("1.000"),
            status=StatusProduto.ATIVO,
        )
        self.pedido = PedidoCompra.objects.create(
            matriz=self.matriz,
            fornecedor=self.fornecedor,
            numero=900001,
            status=StatusPedidoCompra.ENVIADO,
            data_emissao=timezone.localdate(),
            condicao_pagamento="30 dias",
            criado_por=self.usuario,
        )
        self.item = ItemPedidoCompra.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade=Decimal("10.000"),
            valor_unitario=Decimal("10.00"),
        )

    def test_recebimento_exige_vencimento_estruturado_e_gera_titulo_pagar(self):
        vencimento = timezone.localdate() + timedelta(days=30)

        recebimento = receber_pedido_compra(
            pedido=self.pedido,
            loja=self.loja,
            itens=[
                {
                    "item_pedido_id": self.item.pk,
                    "quantidade": Decimal("4.000"),
                }
            ],
            chave_idempotencia="f2b-red-recebimento-001",
            usuario=self.usuario,
            documento_referencia="F2B-RED-001",
            vencimento_financeiro=vencimento,
        )

        titulo = TituloFinanceiro.objects.get(
            natureza="PAGAR",
            origem_tipo="COMPRA_RECEBIMENTO",
            origem_id=recebimento.uuid,
        )
        self.assertEqual(titulo.parcelas.count(), 1)
        parcela = titulo.parcelas.get()
        self.assertEqual(parcela.vencimento, vencimento)
        self.assertEqual(parcela.valor_original, Decimal("40.00"))