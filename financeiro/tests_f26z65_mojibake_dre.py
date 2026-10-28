from pathlib import Path
from django.test import SimpleTestCase
from financeiro.forms import PlanoContaForm
from financeiro.models import PlanoConta

class F26Z65MojibakeDRETests(SimpleTestCase):
    def test_modelo_e_form_expoem_unicode_correto(self):
        campo=PlanoConta._meta.get_field("classificacao_dre")
        self.assertEqual(str(campo.verbose_name), "Classifica\u00e7\u00e3o DRE")
        labels={str(v):str(l) for v,l in campo.choices}
        self.assertEqual(labels["DEDUCAO_RECEITA"], "Dedu\u00e7\u00e3o de receita")
        form=PlanoContaForm()
        self.assertEqual(str(form.fields["classificacao_dre"].label), "Classifica\u00e7\u00e3o DRE")
        escolhas={str(v):str(l) for v,l in form.fields["classificacao_dre"].choices}
        self.assertEqual(escolhas["DEDUCAO_RECEITA"], "Dedu\u00e7\u00e3o de receita")

    def test_fontes_dre_nao_contem_assinaturas_mojibake_corrigidas(self):
        bad=("Classifica\u00c3\u00a7\u00c3\u00a3o DRE","Dedu\u00c3\u00a7\u00c3\u00a3o de receita","Dedu\u00c3\u00a7\u00c3\u00b5es da Receita","Receita L\u00c3\u00adquida")
        for arquivo in ("financeiro/models.py","financeiro/migrations/0008_planoconta_classificacao_dre.py","relatorios/views.py"):
            s=Path(arquivo).read_text(encoding="utf-8")
            for token in bad:
                self.assertNotIn(token,s,arquivo)