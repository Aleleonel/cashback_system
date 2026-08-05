
from pathlib import Path

from django.test import SimpleTestCase


class CadastrosFiscaisUIContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]
        cls.template_root = (
            root
            / "fiscal"
            / "templates"
            / "fiscal"
        )
        cls.css_path = (
            root
            / "fiscal"
            / "static"
            / "fiscal"
            / "css"
            / "cadastros_fiscais.css"
        )
        cls.listas = sorted(
            cls.template_root.rglob("lista.html")
        )
        cls.formularios = sorted(
            cls.template_root.rglob("form.html")
        )

    def test_existencia_dos_templates(self):
        self.assertGreaterEqual(len(self.listas), 10)
        self.assertGreaterEqual(len(self.formularios), 10)

    def test_listas_usam_contrato_visual(self):
        for path in self.listas:
            with self.subTest(template=str(path)):
                text = path.read_text(encoding="utf-8")
                self.assertIn(
                    "fiscal/css/cadastros_fiscais.css",
                    text,
                )
                self.assertIn(
                    'data-fiscal-lista="true"',
                    text,
                )
                self.assertIn(
                    "fiscal-list-card",
                    text,
                )
                self.assertIn(
                    "fiscal-table",
                    text,
                )

    def test_formularios_usam_contrato_visual(self):
        for path in self.formularios:
            with self.subTest(template=str(path)):
                text = path.read_text(encoding="utf-8")
                self.assertIn(
                    "fiscal/css/cadastros_fiscais.css",
                    text,
                )
                self.assertIn(
                    'data-fiscal-formulario="true"',
                    text,
                )
                self.assertIn(
                    "fiscal-form-card",
                    text,
                )
                self.assertIn(
                    "fiscal-form-actions",
                    text,
                )

    def test_css_responsivo_existe(self):
        css = self.css_path.read_text(
            encoding="utf-8"
        )
        self.assertIn(".fiscal-table", css)
        self.assertIn(".fiscal-form-actions", css)
        self.assertIn(
            "@media (max-width: 767.98px)",
            css,
        )
