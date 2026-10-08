from pathlib import Path

from django.test import SimpleTestCase
from django.urls import reverse

ROOT = Path(__file__).resolve().parent.parent


class RelatoriosCadastrosVisualRegressaoTests(SimpleTestCase):
    def test_rota_hub_cadastros(self):
        self.assertEqual(reverse("relatorios:cadastros"), "/relatorios/cadastros/")

    def test_sidebar_expoe_categoria_cadastros(self):
        sidebar = (ROOT / "templates" / "partials" / "sidebar.html").read_text(encoding="utf-8")
        self.assertEqual(sidebar.count("relatorios:cadastros"), 1)

    def test_hub_expoe_clientes_e_aniversariantes(self):
        hub = (ROOT / "relatorios" / "templates" / "relatorios" / "cadastros.html").read_text(encoding="utf-8")
        self.assertEqual(hub.count("relatorios:clientes"), 1)
        self.assertEqual(hub.count("relatorios:aniversariantes"), 1)
        self.assertIn("Relat\u00f3rio de Clientes", hub)
        self.assertIn("Relat\u00f3rio de Aniversariantes", hub)
        self.assertIn("por m\u00eas", hub)

    def test_template_aniversariantes_sem_mojibake(self):
        texto = (ROOT / "relatorios" / "templates" / "relatorios" / "aniversariantes.html").read_text(encoding="utf-8")
        for correto in ("Relat\u00f3rio", "M\u00eas", "Anivers\u00e1rio", "P\u00e1gina", "Pr\u00f3xima"):
            self.assertIn(correto, texto)