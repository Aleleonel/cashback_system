from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = {
    "lancamento_manual": ROOT / "financeiro/templates/financeiro/lancamento_manual.html",
    "plano_conta": ROOT / "financeiro/templates/financeiro/plano_conta_form.html",
    "centro_custo": ROOT / "financeiro/templates/financeiro/centro_custo_form.html",
    "instituicao_bancaria": ROOT / "financeiro/templates/financeiro/instituicao_bancaria_form.html",
    "conta_financeira": ROOT / "financeiro/templates/financeiro/conta_financeira_form.html",
}

class R9KUXVisualContractTests(SimpleTestCase):
    def _text(self, key):
        return TEMPLATES[key].read_text(encoding="utf-8")

    def test_cinco_telas_adotam_contrato_de_pagina_e_acoes(self):
        for key in TEMPLATES:
            with self.subTest(tela=key):
                text = self._text(key)
                self.assertIn("ui-page", text)
                self.assertIn("ui-page-header", text)
                self.assertIn("ui-form-actions", text)

    def test_cinco_telas_nao_usam_form_as_p(self):
        for key in TEMPLATES:
            with self.subTest(tela=key):
                self.assertNotIn("form.as_p", self._text(key))

    def test_cinco_telas_expoem_ajuda_operacional(self):
        for key in TEMPLATES:
            with self.subTest(tela=key):
                text = self._text(key)
                self.assertIn("Como preencher", text)
                self.assertIn("form-text", text)

    def test_cinco_telas_renderizam_campos_explicitamente(self):
        for key in TEMPLATES:
            with self.subTest(tela=key):
                text = self._text(key)
                self.assertIn("form-label", text)
                self.assertTrue(
                    ("{% for field in form %}" in text) or ("form." in text),
                    msg=f"{key} nao possui renderizacao explicita de campos",
                )
                self.assertIn("field.errors", text)

    def test_grid_responsivo_presente_nas_cinco_telas(self):
        for key in TEMPLATES:
            with self.subTest(tela=key):
                text = self._text(key)
                self.assertIn("row", text)
                self.assertTrue(
                    ("g-3" in text) or ("gap-" in text),
                    msg=f"{key} nao explicita espacamento responsivo do formulario",
                )