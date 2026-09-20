from django.test import SimpleTestCase
from financeiro.forms import InstituicaoBancariaForm

class InstituicaoBancariaVisualWidgetsR9KUXTests(SimpleTestCase):
    def test_widgets_usam_classes_visuais_congeladas(self):
        form = InstituicaoBancariaForm()
        esperadas = {
            "codigo_bacen": "form-control",
            "nome": "form-control",
            "ativo": "form-check-input",
        }
        for nome, classe in esperadas.items():
            classes = form.fields[nome].widget.attrs.get("class", "").split()
            self.assertIn(classe, classes, f"{nome} deve usar {classe}")