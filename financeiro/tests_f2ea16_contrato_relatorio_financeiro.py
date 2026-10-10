from pathlib import Path
from django.test import SimpleTestCase

class F2EA16ContratoRelatorioFinanceiroTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("financeiro/views.py").read_text(encoding="utf-8")
        cls.painel = Path("financeiro/templates/financeiro/painel.html").read_text(encoding="utf-8")
        cls.urls_rel = Path("relatorios/urls.py").read_text(encoding="utf-8")
        cls.views_rel = Path("relatorios/views.py").read_text(encoding="utf-8")
        cls.sidebar = Path("templates/partials/sidebar.html").read_text(encoding="utf-8")
        cls.hub_path = Path("relatorios/templates/relatorios/financeiro.html")

    def test_operador_financeiro_deve_usar_loja_operacional_da_sessao(self):
        self.assertIn("loja_operacional_id", self.views)

    def test_operador_nao_deve_receber_seletor_cross_store(self):
        self.assertTrue(
            "pode_filtrar_loja" in self.views or "usuario_operacional" in self.views
        )
        self.assertTrue(
            "pode_filtrar_loja" in self.painel or "usuario_operacional" in self.painel
        )

    def test_hub_financeiro_deve_existir(self):
        self.assertIn("name='financeiro'", self.urls_rel)
        self.assertIn("def hub_financeiro", self.views_rel)
        self.assertTrue(self.hub_path.exists())

    def test_sidebar_relatorios_deve_conter_financeiro(self):
        self.assertIn("relatorios:financeiro", self.sidebar)

    def test_hub_deve_reutilizar_painel_financeiro(self):
        if not self.hub_path.exists():
            self.fail("Hub financeiro ainda nao existe.")
        hub = self.hub_path.read_text(encoding="utf-8")
        self.assertIn("relatorios:financeiro_painel", hub)
