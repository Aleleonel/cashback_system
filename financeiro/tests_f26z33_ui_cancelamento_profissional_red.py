from pathlib import Path
from django.test import SimpleTestCase

class F26Z33ContratoUICancelamentoProfissionalRedTests(SimpleTestCase):
    def setUp(self):
        self.forms=Path("financeiro/forms.py").read_text(encoding="utf-8")
        self.views=Path("financeiro/views.py").read_text(encoding="utf-8")
        self.confirm=Path("financeiro/templates/financeiro/titulo_cancelar_confirm.html").read_text(encoding="utf-8")
        self.detail=Path("financeiro/templates/financeiro/titulo_detalhe.html").read_text(encoding="utf-8")

    def test_formulario_profissional_dedicado(self):
        self.assertIn("class CancelarTituloForm(forms.Form):", self.forms)
        self.assertIn("motivo = forms.CharField(", self.forms)

    def test_view_usa_form_e_preserva_erros(self):
        bloco=self.views[self.views.index("def titulo_cancelar("):]
        bloco=bloco[:bloco.index("\ndef ",5)]
        self.assertIn("CancelarTituloForm(", bloco)
        self.assertIn("form.is_valid()", bloco)
        self.assertIn('"form": form', bloco)

    def test_template_nao_le_post_cru_e_renderiza_form(self):
        self.assertNotIn("request.POST.motivo", self.confirm)
        self.assertIn("form.motivo", self.confirm)

    def test_mensagens_explicam_estorno_e_origem(self):
        baixo=self.confirm.lower()
        self.assertIn("estorno", baixo)
        self.assertIn("origem", baixo)

    def test_detalhe_condiciona_cancelamento_por_regra_explicita(self):
        self.assertIn("pode_cancelar_titulo", self.views)
        self.assertIn("{% if pode_cancelar_titulo %}", self.detail)

    def test_view_bloqueia_origem_automatica_e_competencia_fechada(self):
        bloco=self.views[self.views.index("def titulo_cancelar("):]
        bloco=bloco[:bloco.index("\ndef ",5)]
        self.assertIn("OrigemTipo.MANUAL", bloco)
        self.assertIn("OrigemTipo.AJUSTE", bloco)
        self.assertIn("competencia_gerencial_esta_fechada", bloco)

    def test_templates_sem_mojibake_conhecido(self):
        for texto in (self.confirm,self.detail):
            for token in ("Ý","¾","Ú","þ","Ò","§","ù"):
                self.assertNotIn(token,texto)
