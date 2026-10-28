from django.test import SimpleTestCase
from financeiro.forms import PlanoContaForm
from financeiro.models import PlanoConta

class F26Z63UiClassificacaoDREPlanoTests(SimpleTestCase):
    def test_form_expoe_classificacao_dre(self):
        form = PlanoContaForm()
        self.assertIn("classificacao_dre", form.fields)
        self.assertEqual(
            form.fields["classificacao_dre"].widget.attrs.get("class"),
            "form-select",
        )

    def test_form_expoe_opcoes_oficiais_e_vazio(self):
        form = PlanoContaForm()
        valores = {str(valor) for valor, _rotulo in form.fields["classificacao_dre"].choices}
        self.assertIn("", valores)
        self.assertIn(PlanoConta.ClassificacaoDRE.DEDUCAO_RECEITA, valores)
        self.assertIn(PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL, valores)
        self.assertIn(PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO, valores)
        self.assertIn(PlanoConta.ClassificacaoDRE.OUTRA_RECEITA_DESPESA, valores)
