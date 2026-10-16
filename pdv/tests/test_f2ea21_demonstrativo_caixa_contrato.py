from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]

class F2EA21DemonstrativoCaixaContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.urls=(ROOT/"pdv"/"urls.py").read_text(encoding="utf-8")
        cls.views=(ROOT/"pdv"/"views.py").read_text(encoding="utf-8")
        cls.sidebar=(ROOT/"templates"/"partials"/"sidebar.html").read_text(encoding="utf-8")

    def test_rota_detalhe_sessao_existe(self):
        self.assertIn('name="demonstrativo_caixa"', self.urls)
        self.assertIn("def demonstrativo_caixa(request,", self.views)

    def test_demonstrativo_e_somente_leitura_e_usa_sessao(self):
        self.assertIn("SessaoCaixa", self.views)
        self.assertIn("PagamentoVenda", self.views)
        self.assertIn("MovimentacaoCaixa", self.views)

    def test_relatorio_caixa_aparece_na_area_relatorios(self):
        self.assertIn("Caixa", self.sidebar)
        self.assertIn("historico_fechamentos", self.sidebar)
