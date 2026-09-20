from django.test import SimpleTestCase
from financeiro.forms import ContaFinanceiraForm

class ContaFinanceiraVisualWidgetsR9KUXTests(SimpleTestCase):
    def test_widgets_usam_classes_visuais_congeladas(self):
        form = ContaFinanceiraForm()
        esperadas = {
            "loja": "form-select",
            "instituicao": "form-select",
            "tipo": "form-select",
            "nome": "form-control",
            "agencia": "form-control",
            "numero": "form-control",
            "ativo": "form-check-input",
        }
        for nome, classe in esperadas.items():
            classes = form.fields[nome].widget.attrs.get("class", "").split()
            self.assertIn(classe, classes, f"{nome} deve usar {classe}")