from pathlib import Path
from django.test import SimpleTestCase

class F2EA21PdfDemonstrativoContratoTests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.urls = (root / "pdv" / "urls.py").read_text(encoding="utf-8")
        self.views = (root / "pdv" / "views.py").read_text(encoding="utf-8")
        self.template = (root / "pdv" / "templates" / "pdv" / "demonstrativo_caixa.html").read_text(encoding="utf-8")

    def test_rota_pdf_existe(self):
        self.assertIn('name="demonstrativo_caixa_pdf"', self.urls)

    def test_view_pdf_existe(self):
        self.assertIn("def demonstrativo_caixa_pdf(request, sessao_id):", self.views)

    def test_pdf_usa_reportlab(self):
        self.assertIn("reportlab", self.views)

    def test_resposta_pdf(self):
        self.assertIn("application/pdf", self.views)
        self.assertIn("Content-Disposition", self.views)

    def test_tela_expoe_exportacao_pdf(self):
        self.assertIn("demonstrativo_caixa_pdf", self.template)
        self.assertIn("PDF", self.template)
