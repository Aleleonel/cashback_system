from pathlib import Path
from django.test import SimpleTestCase

class F26Z51RecalculoValorFinalEdicaoTests(SimpleTestCase):
    def setUp(self):
        self.template = Path("financeiro/templates/financeiro/titulo_editar.html").read_text(encoding="utf-8")

    def test_edicao_recalcula_valor_final_no_cliente(self):
        for campo in ("id_valor_bruto", "id_valor_desconto", "id_valor_juros", "id_valor_final"):
            self.assertIn(campo, self.template)
        self.assertIn('document.addEventListener("DOMContentLoaded", function () {', self.template)
        self.assertIn('addEventListener("input", recalcularValorFinal)', self.template)
        self.assertIn('addEventListener("change", recalcularValorFinal)', self.template)
        self.assertIn("valueAsNumber", self.template)
        self.assertIn("numeroDoCampo(campos[0]) - numeroDoCampo(campos[1]) + numeroDoCampo(campos[2])", self.template)

    def test_valor_final_continua_derivado_no_backend(self):
        forms = Path("financeiro/forms.py").read_text(encoding="utf-8")
        self.assertIn("valor_final = valor_bruto - valor_desconto + valor_juros", forms)
        self.assertIn('cleaned_data["valor_final"] = valor_final', forms)
