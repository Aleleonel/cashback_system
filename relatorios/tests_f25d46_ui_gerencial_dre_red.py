from pathlib import Path
from django.test import SimpleTestCase

class DREUIGerencialRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root=Path(__file__).resolve().parents[1]
        cls.template=(root/"relatorios"/"templates"/"relatorios"/"dre.html").read_text(encoding="utf-8")
        cls.service=(root/"relatorios"/"services_dre.py").read_text(encoding="utf-8")
        cls.financeiro=(root/"relatorios"/"templates"/"relatorios"/"financeiro.html").read_text(encoding="utf-8")

    def test_expoe_cards_de_margens(self):
        self.assertIn("resultado.margem_bruta", self.template)
        self.assertIn("resultado.margem_operacional", self.template)

    def test_comparativo_expoe_variacao_absoluta_e_percentual(self):
        self.assertIn("comparativo.variacao_absoluta", self.template)
        self.assertIn("comparativo.variacao_percentual", self.template)

    def test_comparativo_cobre_linhas_gerenciais(self):
        for campo in (
            "receita_bruta","deducoes_receita","receita_liquida","cmv","lucro_bruto",
            "despesas_operacionais","resultado_operacional","resultado_financeiro",
            "outras_receitas_despesas","resultado_antes_impostos",
        ):
            self.assertIn(f"comparativo.atual.{campo}", self.template)

    def test_drilldown_direto_expoe_origens_reais(self):
        for token in ("drilldown.receita_bruta.vendas","drilldown.cmv.itens_venda",
                      "drilldown.despesas_operacionais.titulos",
                      "drilldown.resultado_financeiro.titulos"):
            self.assertIn(token, self.template)

    def test_drilldown_derivado_expoe_formula_e_componentes(self):
        self.assertIn(".formula", self.template)
        self.assertIn(".componentes", self.template)

    def test_evolucao_expoe_mais_que_resultado_final(self):
        self.assertIn("item.resultado.receita_liquida", self.template)
        self.assertIn("item.resultado.lucro_bruto", self.template)
        self.assertIn("item.resultado.resultado_operacional", self.template)

    def test_hub_financeiro_tem_acesso_dre(self):
        self.assertIn("relatorios:dre", self.financeiro)

    def test_remove_datetime_import_hack(self):
        self.assertNotIn('__import__("datetime").timedelta', self.service)
