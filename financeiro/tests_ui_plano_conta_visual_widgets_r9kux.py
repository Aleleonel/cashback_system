from django.test import SimpleTestCase
from financeiro.forms import PlanoContaForm

class PlanoContaVisualWidgetsR9KUXTests(SimpleTestCase):
    def test_widgets_usam_classes_visuais_congeladas(self):
        form = PlanoContaForm()
        esperadas = {
            "codigo": "form-control",
            "nome": "form-control",
            "tipo": "form-select",
            "natureza": "form-select",
            "pai": "form-select",
            "aceita_lancamento": "form-check-input",
            "ativo": "form-check-input",
        }
        for nome, classe in esperadas.items():
            classes = form.fields[nome].widget.attrs.get("class", "").split()
            self.assertIn(classe, classes, f"{nome} deve usar {classe}")