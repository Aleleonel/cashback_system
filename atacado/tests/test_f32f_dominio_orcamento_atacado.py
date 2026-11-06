from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from atacado.models import (
    ItemOrcamentoAtacado,
    OrcamentoAtacado,
    StatusOrcamentoAtacado,
    TransicaoOrcamentoAtacado,
)
from atacado.services import expirar_orcamento_se_necessario, transicionar_orcamento
from clientes.models import Cliente
from empresas.models import Loja, Matriz
from produtos.models import Produto, UnidadeMedida


class F32FDominioOrcamentoAtacadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz F32F")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja F32F")
        cls.cliente = Cliente.objects.create(
            matriz=cls.matriz,
            loja_cadastro=cls.loja,
            nome="Cliente F32F",
        )
        cls.unidade = UnidadeMedida.objects.create(matriz=cls.matriz, sigla="UN", descricao="Unidade")
        cls.produto = Produto.objects.create(
            matriz=cls.matriz,
            unidade_medida=cls.unidade,
            codigo_interno="F32F-001",
            nome="Produto F32F",
            custo_base=Decimal("50.00"),
            preco_venda=Decimal("100.00"),
        )

    def novo_orcamento(self, **extra):
        dados = {
            "matriz": self.matriz,
            "loja": self.loja,
            "cliente": self.cliente,
            "valido_ate": timezone.now() + timedelta(days=7),
        }
        dados.update(extra)
        return OrcamentoAtacado.objects.create(**dados)

    def test_status_inicial_e_rascunho(self):
        o = self.novo_orcamento()
        self.assertEqual(o.status, StatusOrcamentoAtacado.RASCUNHO)

    def test_fluxo_principal_rascunho_enviado_aprovado_pedido(self):
        o = self.novo_orcamento()
        transicionar_orcamento(o, StatusOrcamentoAtacado.ENVIADO)
        transicionar_orcamento(o, StatusOrcamentoAtacado.APROVADO)
        transicionar_orcamento(o, StatusOrcamentoAtacado.PEDIDO_GERADO)
        self.assertEqual(o.status, StatusOrcamentoAtacado.PEDIDO_GERADO)
        self.assertEqual(TransicaoOrcamentoAtacado.objects.filter(orcamento=o).count(), 3)

    def test_transicao_invalida_e_rejeitada(self):
        o = self.novo_orcamento()
        with self.assertRaises(ValidationError):
            transicionar_orcamento(o, StatusOrcamentoAtacado.PEDIDO_GERADO)

    def test_orcamento_expirado_nao_pode_ser_aprovado(self):
        o = self.novo_orcamento(valido_ate=timezone.now() - timedelta(minutes=1))
        transicionar_orcamento(o, StatusOrcamentoAtacado.ENVIADO)
        with self.assertRaises(ValidationError):
            transicionar_orcamento(o, StatusOrcamentoAtacado.APROVADO)

    def test_expiracao_automatica_de_enviado(self):
        o = self.novo_orcamento(valido_ate=timezone.now() - timedelta(minutes=1))
        transicionar_orcamento(o, StatusOrcamentoAtacado.ENVIADO)
        expirar_orcamento_se_necessario(o)
        self.assertEqual(o.status, StatusOrcamentoAtacado.EXPIRADO)

    def test_item_preserva_snapshot_comercial_basico(self):
        o = self.novo_orcamento()
        item = ItemOrcamentoAtacado.objects.create(
            orcamento=o,
            produto=self.produto,
            quantidade=Decimal("2.000"),
            preco_unitario_original=Decimal("100.00"),
            preco_unitario_base=Decimal("90.00"),
            preco_unitario_final=Decimal("85.00"),
            percentual_desconto_atacado=Decimal("5.0000"),
            desconto_atacado=Decimal("10.00"),
            ajuste_negociado=Decimal("-0.00"),
            produto_promocional=True,
            atacado_elegivel=False,
            conta_para_enquadramento=True,
            justificativa_negociacao="Condição negociada.",
        )
        self.assertEqual(item.subtotal, Decimal("180.00"))
        self.assertEqual(item.total_final, Decimal("170.00"))
        self.assertTrue(item.produto_promocional)
        self.assertFalse(item.atacado_elegivel)

    def test_recalculo_totais_mantem_frete_separado(self):
        o = self.novo_orcamento(frete=Decimal("25.00"))
        ItemOrcamentoAtacado.objects.create(
            orcamento=o,
            produto=self.produto,
            quantidade=Decimal("2.000"),
            preco_unitario_original=Decimal("100.00"),
            preco_unitario_base=Decimal("100.00"),
            preco_unitario_final=Decimal("90.00"),
            desconto_atacado=Decimal("20.00"),
        )
        o.recalcular_totais()
        self.assertEqual(o.subtotal_produtos, Decimal("200.00"))
        self.assertEqual(o.desconto_atacado, Decimal("20.00"))
        self.assertEqual(o.frete, Decimal("25.00"))
        self.assertEqual(o.total, Decimal("205.00"))
