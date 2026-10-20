from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[1]

class DREProfissionalContratoRedTests(SimpleTestCase):
    def _ler(self, relativo):
        p = ROOT / relativo
        self.assertTrue(p.exists(), f"Arquivo obrigatorio ausente: {relativo}")
        return p.read_text(encoding="utf-8")

    def test_servico_dre_profissional_existe(self):
        codigo = self._ler("relatorios/services_dre.py")
        for token in (
            "def apurar_dre",
            "receita_bruta",
            "deducoes_receita",
            "receita_liquida",
            "cmv",
            "lucro_bruto",
            "despesas_operacionais",
            "resultado_operacional",
            "resultado_financeiro",
            "outras_receitas_despesas",
            "resultado_antes_impostos",
        ):
            self.assertIn(token, codigo)

    def test_dre_declara_regime_competencia_e_nao_caixa(self):
        codigo = self._ler("relatorios/services_dre.py")
        self.assertIn("data_competencia", codigo)
        self.assertIn("finalizada_em", codigo)
        self.assertNotIn("data_baixa__range", codigo)

    def test_cmv_usa_snapshot_historico(self):
        codigo = self._ler("relatorios/services_dre.py")
        self.assertIn("custo_unitario_snapshot", codigo)
        self.assertNotIn("produto__custo_base", codigo)

    def test_dre_possui_analise_vertical_e_comparativo(self):
        codigo = self._ler("relatorios/services_dre.py")
        for token in ("analise_vertical", "comparativo", "margem_bruta", "margem_operacional"):
            self.assertIn(token, codigo)

    def test_dre_possui_drilldown_rastreavel(self):
        codigo = self._ler("relatorios/services_dre.py")
        for token in ("drilldown", "origem_tipo", "origens_por_linha"):
            self.assertIn(token, codigo)

    def test_dre_respeita_matriz_loja_e_centro_custo(self):
        codigo = self._ler("relatorios/services_dre.py")
        for token in ("matriz", "loja", "centro_custo"):
            self.assertIn(token, codigo)

    def test_dre_tem_view_url_template_e_exportacoes(self):
        urls = self._ler("relatorios/urls.py")
        views = self._ler("relatorios/views.py")
        template = self._ler("relatorios/templates/relatorios/dre.html")
        self.assertIn("dre", urls.lower())
        self.assertIn("dre", views.lower())
        self.assertIn("dre", template.lower())
        self.assertIn("pdf", views.lower())
        self.assertIn("xlsx", views.lower())

    def test_dre_nao_depende_de_fiscal_para_contrato_inicial(self):
        codigo = self._ler("relatorios/services_dre.py")
        self.assertNotIn("from fiscal", codigo)
        self.assertNotIn("import fiscal", codigo)