from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse

class CentralFiscalUIContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]
        cls.template = (root/"fiscal"/"templates"/"fiscal"/"inicio.html").read_text(encoding="utf-8")
        cls.views = (root/"fiscal"/"views.py").read_text(encoding="utf-8")
        cls.css = (root/"fiscal"/"static"/"fiscal"/"css"/"central_fiscal.css").read_text(encoding="utf-8")

    def test_rota_central_fiscal_permanece_estavel(self):
        self.assertEqual(reverse("fiscal:inicio"), "/fiscal/")

    def test_template_possui_secoes_premium(self):
        for trecho in ("data-central-fiscal", "Fundacao fiscal ativa",
            "ainda nao esta liberada",
            "Indicadores fiscais", "Referências tributárias", "Benefícios e regras fiscais", "Próximas integrações", "modulos_referencia", "modulos_inteligencia", "proximas_etapas"):
            self.assertIn(trecho, self.template)

    def test_template_carrega_css_especifico(self):
        self.assertIn("fiscal/css/central_fiscal.css", self.template)

    def test_view_fornece_indicadores_e_grupos(self):
        for trecho in ('"indicadores": indicadores', '"modulos_referencia": referencias', '"modulos_inteligencia": inteligencia', '"proximas_etapas": proximas_etapas', '"modulos": todos'):
            self.assertIn(trecho, self.views)

    def test_view_mantem_permissoes(self):
        self.assertIn("@require_permission(PERMISSAO_FISCAL_VISUALIZAR)", self.views)
        self.assertIn("PERMISSAO_FISCAL_GERENCIAR_CADASTROS", self.views)

    def test_css_possui_responsividade(self):
        self.assertIn("@media(max-width:767.98px)", self.css)
        self.assertIn(".fiscal-module-card:hover", self.css)
