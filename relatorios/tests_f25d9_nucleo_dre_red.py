from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "relatorios" / "services_dre.py"


class F25D9NucleoDREContratoRedTests(SimpleTestCase):
    def fonte(self):
        self.assertTrue(
            SERVICE.exists(),
            "F25D9 exige relatorios/services_dre.py como nucleo economico explicito da DRE.",
        )
        return SERVICE.read_text(encoding="utf-8-sig")

    def test_servico_declara_regime_competencia(self):
        fonte = self.fonte()
        self.assertIn("REGIME_COMPETENCIA", fonte)
        self.assertNotIn("BaixaFinanceira", fonte)

    def test_receita_e_cmv_nascem_da_venda_finalizada(self):
        fonte = self.fonte()
        for token in (
            "Venda",
            "StatusOperacaoVenda.FINALIZADA",
            "finalizada_em",
            "subtotal",
            "desconto",
            "acrescimo",
            "custo_unitario_snapshot",
            "cancelado=False",
        ):
            self.assertIn(token, fonte)

    def test_contrato_formula_receita(self):
        fonte = self.fonte()
        for token in (
            "receita_bruta",
            "deducoes_receita",
            "receita_liquida",
            "acrescimos",
        ):
            self.assertIn(token, fonte)

    def test_compra_recebimento_nao_vira_cmv_nem_despesa_automaticamente(self):
        fonte = self.fonte()
        self.assertIn("COMPRA_RECEBIMENTO", fonte)
        self.assertIn("EXCLUIR_COMPRA_RECEBIMENTO_DRE", fonte)

    def test_financeiro_exige_classificacao_dre_explicita(self):
        fonte = self.fonte()
        self.assertIn("classificacao_dre", fonte)
        for token in (
            "DEDUCAO_RECEITA",
            "DESPESA_OPERACIONAL",
            "RESULTADO_FINANCEIRO",
            "OUTRA_RECEITA_DESPESA",
        ):
            self.assertIn(token, fonte)

    def test_titulo_cancelado_nao_compÃµe_dre(self):
        fonte = self.fonte()
        self.assertIn("TituloFinanceiro.Status.CANCELADO", fonte)

    def test_competencia_financeira_usa_data_competencia(self):
        fonte = self.fonte()
        self.assertIn("data_competencia", fonte)

    def test_comissao_economica_vem_do_snapshot_de_fechamento(self):
        fonte = self.fonte()
        for token in (
            "ComissaoVendedor",
            "FechamentoComissao",
            "competencia_ano",
            "competencia_mes",
            "valor_comissao",
        ):
            self.assertIn(token, fonte)
        self.assertIn("COMISSAO_SNAPSHOT", fonte)

    def test_nao_usa_titulo_venda_pagamento_como_receita_operacional(self):
        fonte = self.fonte()
        self.assertIn("VENDA_PAGAMENTO", fonte)
        self.assertIn("EXCLUIR_VENDA_PAGAMENTO_RECEITA", fonte)

    def test_devolucao_venda_nao_e_inventada(self):
        fonte = self.fonte()
        self.assertIn("DEVOLUCAO_VENDA_NAO_IMPLEMENTADA", fonte)

    def test_servico_declara_estrutura_minima_dre(self):
        fonte = self.fonte()
        for token in (
            "lucro_bruto",
            "despesas_operacionais",
            "resultado_operacional",
            "resultado_financeiro",
            "outras_receitas_despesas",
            "resultado_antes_impostos",
        ):
            self.assertIn(token, fonte)