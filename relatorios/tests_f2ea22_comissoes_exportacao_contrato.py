from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent


class ExportacaoComissoesContratoTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = (ROOT / "relatorios" / "views.py").read_text(encoding="utf-8")
        cls.urls = (ROOT / "relatorios" / "urls.py").read_text(encoding="utf-8")
        cls.template = (
            ROOT / "relatorios" / "templates" / "relatorios" / "relatorio_comissoes.html"
        ).read_text(encoding="utf-8")

    def test_pdf_tem_rota_e_content_type(self):
        self.assertIn("exportar_comissoes_pdf", self.urls)
        self.assertIn("application/pdf", self.views)
        self.assertIn("reportlab", self.views)

    def test_xlsx_tem_rota_e_content_type(self):
        self.assertIn("exportar_comissoes_xlsx", self.urls)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            self.views,
        )
        self.assertIn("openpyxl", self.views)

    def test_exportacoes_expoem_download_na_tela(self):
        self.assertIn("exportar_comissoes_pdf", self.template)
        self.assertIn("exportar_comissoes_xlsx", self.template)

    def test_exportacoes_preservam_filtros(self):
        self.assertIn("query_string", self.template)
        self.assertIn("loja", self.views)
        self.assertIn("mes", self.views)
        self.assertIn("ano", self.views)

    def test_exportacoes_usam_snapshots_persistidos(self):
        self.assertIn("FechamentoComissao", self.views)
        self.assertIn("ComissaoVendedor", self.views)
        self.assertNotIn("fechar_comissao", self.views)