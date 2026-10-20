from datetime import date
from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase


class F25D11ContratoCalculoDREFuncionalTests(SimpleTestCase):
    """RED funcional antes de alterar novamente o nucleo de producao."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.codigo = (Path(__file__).resolve().parent / "services_dre.py").read_text(encoding="utf-8")

    def test_venda_finalizada_e_item_ativo_formam_receita_e_cmv(self):
        for token in (
            "StatusOperacaoVenda.FINALIZADA",
            "cancelada_em__isnull=True",
            "cancelado=False",
            'F("quantidade") * F("custo_unitario_snapshot")',
        ):
            self.assertIn(token, self.codigo)

    def test_receita_nao_nasce_do_titulo_de_venda(self):
        self.assertIn("EXCLUIR_VENDA_PAGAMENTO_RECEITA", self.codigo)
        self.assertIn("VENDA_PAGAMENTO", self.codigo)

    def test_compra_recebimento_nao_vira_cmv_ou_despesa(self):
        self.assertIn("EXCLUIR_COMPRA_RECEBIMENTO_DRE", self.codigo)
        self.assertIn("COMPRA_RECEBIMENTO", self.codigo)

    def test_competencia_financeira_e_classificacao_explicita(self):
        self.assertIn("data_competencia__gte=inicio", self.codigo)
        self.assertIn("data_competencia__lte=fim", self.codigo)
        self.assertIn("plano_conta__classificacao_dre__isnull=False", self.codigo)

    def test_titulo_cancelado_e_excluido(self):
        self.assertIn("TituloFinanceiro.Status.CANCELADO", self.codigo)

    def test_comissao_vem_do_fechamento_e_nao_do_pagamento(self):
        self.assertIn("FechamentoComissao", self.codigo)
        self.assertIn("ComissaoVendedor", self.codigo)
        self.assertIn("valor_comissao", self.codigo)
        self.assertIn("TituloFinanceiro.OrigemTipo.COMISSAO", self.codigo)

    def test_filtros_matriz_loja_centro_custo_estao_no_contrato(self):
        self.assertIn("matriz=matriz", self.codigo)
        self.assertIn("loja=loja", self.codigo)
        self.assertIn("centro_custo=centro_custo", self.codigo)

    def test_formula_resultado_esta_explicita(self):
        for token in (
            "receita_liquida = receita_bruta - deducoes_receita",
            "lucro_bruto = receita_liquida - cmv",
            "resultado_operacional = lucro_bruto - despesas_operacionais",
            "resultado_antes_impostos",
        ):
            self.assertIn(token, self.codigo)

    def test_api_funcional_deve_expor_memoria_de_calculo_rastreavel(self):
        # RED intencional: o proximo passo deve sair de simples totais para
        # memoria de calculo reconciliavel com as operacoes de origem.
        for token in (
            "memoria_calculo",
            "origens_receita",
            "origens_cmv",
            "origens_despesas",
        ):
            self.assertIn(token, self.codigo)

    def test_api_funcional_deve_expor_margens(self):
        # RED intencional para indicadores gerenciais do nucleo.
        for token in ("margem_bruta", "margem_operacional"):
            self.assertIn(token, self.codigo)