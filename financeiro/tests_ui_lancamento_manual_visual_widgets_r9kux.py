from django.test import SimpleTestCase
from financeiro.forms import LancamentoManualForm

class LancamentoManualVisualWidgetsR9KUXTests(SimpleTestCase):
    def test_widgets_usam_classes_do_design_system(self):
        form = LancamentoManualForm()
        selects = ("natureza", "loja", "plano_conta", "centro_custo")
        controls = (
            "entidade_nome", "documento_referencia", "data_emissao",
            "data_competencia", "data_vencimento", "valor_bruto",
            "valor_desconto", "valor_juros", "valor_final",
            "numero_parcelas", "observacao",
        )
        for name in selects:
            classes = form.fields[name].widget.attrs.get("class", "").split()
            self.assertIn("form-select", classes, f"{name} deve usar form-select")
        for name in controls:
            classes = form.fields[name].widget.attrs.get("class", "").split()
            self.assertIn("form-control", classes, f"{name} deve usar form-control")