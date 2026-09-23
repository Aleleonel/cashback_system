from django.test import SimpleTestCase
from pathlib import Path


class R17ExportacaoCsvRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base = Path(__file__).resolve().parent
        cls.views = (base / "views.py").read_text(encoding="utf-8")
        cls.urls = (base / "urls.py").read_text(encoding="utf-8")
        cls.template = (base / "templates" / "financeiro" / "titulos.html").read_text(encoding="utf-8")

    def test_rota_exportacao_csv_existe(self):
        self.assertIn('name="titulos_exportar_csv"', self.urls)

    def test_view_exportacao_exige_permissao_visualizar(self):
        inicio = self.views.index("def titulos_exportar_csv")
        trecho = self.views[max(0, inicio - 300):inicio + 1800]
        self.assertIn("@login_required", trecho)
        self.assertIn("@require_permission(PERMISSAO_FINANCEIRO_VISUALIZAR)", trecho)

    def test_view_revalida_matriz_escopo_e_reutiliza_selector(self):
        inicio = self.views.index("def titulos_exportar_csv")
        trecho = self.views[inicio:inicio + 2600]
        self.assertIn("_matriz_usuario(request)", trecho)
        self.assertIn("_resolver_escopo(request, matriz)", trecho)
        self.assertIn("listar_titulos(", trecho)

    def test_view_aplica_natureza_status_sem_paginacao(self):
        inicio = self.views.index("def titulos_exportar_csv")
        trecho = self.views[inicio:inicio + 2600]
        self.assertIn('request.GET.get("natureza")', trecho)
        self.assertIn('request.GET.get("status")', trecho)
        self.assertNotIn("Paginator(", trecho)

    def test_resposta_e_csv_para_download(self):
        inicio = self.views.index("def titulos_exportar_csv")
        trecho = self.views[inicio:inicio + 3000]
        self.assertIn("text/csv", trecho)
        self.assertIn("Content-Disposition", trecho)
        self.assertIn("csv.writer", trecho)

    def test_template_oferece_exportacao_preservando_filtros(self):
        self.assertIn("titulos_exportar_csv", self.template)
        self.assertIn("natureza={{ natureza }}", self.template)
        self.assertIn("status={{ status }}", self.template)
        self.assertIn("escopo={{ escopo }}", self.template)
        self.assertIn("loja={{ loja.pk }}", self.template)