from django.test import SimpleTestCase

from financeiro.forms import BaixaDinheiroForm


class R10UIBaixaNaoDinheiroREDTests(SimpleTestCase):
    def test_formulario_expoe_forma_pagamento_e_conta_financeira(self):
        form = BaixaDinheiroForm()
        self.assertIn("forma_pagamento", form.fields)
        self.assertIn("conta_financeira", form.fields)

    def test_template_nao_fixa_baixa_como_dinheiro(self):
        with open(
            "financeiro/templates/financeiro/parcela_baixa_form.html",
            encoding="utf-8",
        ) as arquivo:
            template = arquivo.read()
        self.assertNotIn("Registrar baixa em dinheiro", template)
        self.assertIn("form.forma_pagamento", template)
        self.assertIn("form.conta_financeira", template)

    def test_view_nao_restringe_fluxo_a_forma_dinheiro(self):
        with open("financeiro/views.py", encoding="utf-8") as arquivo:
            views = arquivo.read()
        inicio = views.index("def parcela_baixa_nova(")
        trecho = views[inicio:inicio + 6500]
        self.assertNotIn("formas_dinheiro = FormaPagamento.objects.filter(", trecho)
        self.assertIn('form.cleaned_data["forma_pagamento"]', trecho)
        self.assertIn('form.cleaned_data["conta_financeira"]', trecho)