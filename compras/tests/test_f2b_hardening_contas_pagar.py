from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from empresas.models import Loja, Matriz
from estoque.models import SaldoEstoque
from produtos.choices import OrigemPreco, StatusProduto
from produtos.models import Categoria, Marca, Produto, UnidadeMedida
from compras.choices import StatusFornecedor, StatusPedidoCompra
from compras.models import Fornecedor, ItemPedidoCompra, PedidoCompra, RecebimentoCompra
from compras.services.recebimentos import receber_pedido_compra
from financeiro.models import TituloFinanceiro

Usuario = get_user_model()


class F2BHardeningContasPagarTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F2B Hardening")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F2B Hardening")
        self.usuario = Usuario.objects.create_user(
            username="usuario_f2b_hardening", password="senha-segura", matriz=self.matriz
        )
        self.fornecedor = Fornecedor.objects.create(
            matriz=self.matriz,
            razao_social="Fornecedor F2B Hardening LTDA",
            cnpj="88777666000155",
            status=StatusFornecedor.ATIVO,
        )
        categoria = Categoria.objects.create(matriz=self.matriz, nome="Categoria F2B Hardening")
        marca = Marca.objects.create(
            matriz=self.matriz, nome="Marca F2B Hardening", fabricante="Fabricante F2B"
        )
        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz, sigla="UN", descricao="Unidade"
        )
        self.produto = Produto.objects.create(
            matriz=self.matriz,
            categoria=categoria,
            marca=marca,
            unidade_medida=unidade,
            codigo_interno="F2B-HARD-001",
            sku="F2B-HARD-SKU-001",
            gtin="7898877665544",
            ncm="21069030",
            nome="Produto F2B Hardening",
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
            numero=900002,
            status=StatusPedidoCompra.ENVIADO,
            data_emissao=timezone.localdate(),
            condicao_pagamento="texto legado nao interpretar",
            criado_por=self.usuario,
        )
        self.item = ItemPedidoCompra.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade=Decimal("10.000"),
            valor_unitario=Decimal("10.00"),
        )
        self.vencimento = timezone.localdate() + timedelta(days=30)

    def receber(self, quantidade, chave, vencimento_marker=True):
        kwargs = dict(
            pedido=self.pedido,
            loja=self.loja,
            itens=[{"item_pedido_id": self.item.pk, "quantidade": Decimal(quantidade)}],
            chave_idempotencia=chave,
            usuario=self.usuario,
        )
        if vencimento_marker:
            kwargs["vencimento_financeiro"] = self.vencimento
        return receber_pedido_compra(**kwargs)

    def test_vencimento_financeiro_estruturado_e_obrigatorio(self):
        with self.assertRaises(ValidationError):
            self.receber("4.000", "f2b-hard-sem-vencimento", vencimento_marker=False)
        self.assertFalse(RecebimentoCompra.objects.exists())
        self.assertFalse(TituloFinanceiro.objects.exists())

    def test_repeticao_mesma_chave_nao_duplica_recebimento_estoque_ou_titulo(self):
        primeiro = self.receber("4.000", "f2b-hard-idem")
        segundo = self.receber("4.000", "f2b-hard-idem")
        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(RecebimentoCompra.objects.count(), 1)
        self.assertEqual(
            TituloFinanceiro.objects.filter(
                natureza=TituloFinanceiro.Natureza.PAGAR,
                origem_tipo=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO,
                origem_id=str(primeiro.uuid),
            ).count(),
            1,
        )
        saldo = SaldoEstoque.objects.get(
            matriz=self.matriz, loja=self.loja, produto=self.produto
        )
        self.assertEqual(saldo.quantidade_atual, Decimal("4.000"))

    def test_dois_recebimentos_parciais_geram_titulos_independentes(self):
        primeiro = self.receber("4.000", "f2b-hard-parcial-1")
        segundo = self.receber("3.000", "f2b-hard-parcial-2")
        t1 = TituloFinanceiro.objects.get(
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO,
            origem_id=str(primeiro.uuid),
        )
        t2 = TituloFinanceiro.objects.get(
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO,
            origem_id=str(segundo.uuid),
        )
        self.assertNotEqual(t1.pk, t2.pk)
        self.assertEqual(t1.valor_original, Decimal("40.00"))
        self.assertEqual(t2.valor_original, Decimal("30.00"))

    def test_falha_financeira_reverte_recebimento_e_estoque(self):
        with patch(
            "compras.services.recebimentos.criar_titulo_financeiro",
            side_effect=ValidationError({"financeiro": "falha controlada F2B"}),
        ):
            with self.assertRaises(ValidationError):
                self.receber("4.000", "f2b-hard-atomicidade")
        self.assertFalse(RecebimentoCompra.objects.exists())
        self.assertFalse(TituloFinanceiro.objects.exists())
        self.item.refresh_from_db()
        self.pedido.refresh_from_db()
        self.assertEqual(self.item.quantidade_recebida, Decimal("0.000"))
        self.assertEqual(self.pedido.status, StatusPedidoCompra.ENVIADO)
        self.assertFalse(
            SaldoEstoque.objects.filter(
                matriz=self.matriz, loja=self.loja, produto=self.produto
            ).exists()
        )
    def test_valor_recebido_zero_nao_cria_titulo_financeiro(self):
        self.item.valor_unitario = Decimal('0.00')
        self.item.save(update_fields=['valor_unitario', 'atualizado_em'])
        recebimento = receber_pedido_compra(
            pedido=self.pedido,
            loja=self.loja,
            itens=[{
                'item_pedido_id': self.item.pk,
                'quantidade': Decimal('4.000'),
            }],
            chave_idempotencia='f2b-zero-sem-titulo',
            vencimento_financeiro=timezone.localdate(),
            usuario=self.usuario,
        )
        self.assertIsNotNone(recebimento.pk)
        self.assertFalse(
            TituloFinanceiro.objects.filter(
                natureza=TituloFinanceiro.Natureza.PAGAR,
                origem_tipo=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO,
                origem_id=str(recebimento.uuid),
            ).exists()
        )
