from pathlib import Path
from django.test import SimpleTestCase

ROOT=Path(__file__).resolve().parents[1]
VIEWS=(ROOT/"relatorios"/"views.py").read_text(encoding="utf-8")
TPL=(ROOT/"relatorios"/"templates"/"relatorios"/"dre.html").read_text(encoding="utf-8")

class DREValidacaoFiltrosUIExportREDTests(SimpleTestCase):
    def test_contexto_preserva_input_bruto_datas(self):
        self.assertIn('"data_inicio_input"',VIEWS)
        self.assertIn('"data_fim_input"',VIEWS)

    def test_contexto_expoe_flag_filtros_validos(self):
        self.assertIn('"filtros_validos"',VIEWS)

    def test_filtro_invalido_nao_apura_dre(self):
        self.assertIn("if not erro_filtros:",VIEWS)
        self.assertNotIn("resultado_neutro",VIEWS)
        self.assertIn('"resultado": apuracao["resultado"] if apuracao else None',VIEWS)

    def test_template_exibe_erros_de_filtro(self):
        self.assertIn("erro_filtros",TPL)
        self.assertTrue("alert-danger" in TPL or "alert-warning" in TPL)

    def test_template_usa_valores_brutos_nos_inputs_data(self):
        self.assertIn("data_inicio_input",TPL)
        self.assertIn("data_fim_input",TPL)

    def test_template_oculta_resultado_quando_filtros_invalidos(self):
        self.assertIn("filtros_validos",TPL)

    def test_pdf_rejeita_filtros_invalidos(self):
        trecho=VIEWS[VIEWS.index("def exportar_dre_pdf"):VIEWS.index("def exportar_dre_xlsx")]
        self.assertIn("erro_filtros",trecho)
        self.assertIn("status=400",trecho)

    def test_excel_rejeita_filtros_invalidos(self):
        inicio=VIEWS.index("def exportar_dre_xlsx")
        trecho=VIEWS[inicio:]
        self.assertIn("erro_filtros",trecho)
        self.assertIn("status=400",trecho)

    def test_exportacao_sem_matriz_superuser_rejeitada(self):
        self.assertGreaterEqual(VIEWS.count("status=400"),2)