from django.test import SimpleTestCase
from pathlib import Path

class F26Z48GuardaViewAjusteTests(SimpleTestCase):
    def test_view_edicao_admite_manual_e_ajuste(self):
        x=Path("financeiro/views.py").read_text(encoding="utf-8")
        b=x[x.index("def titulo_editar("):x.index("def titulo_cancelar(")]
        self.assertIn("origem_tipo not in {TituloFinanceiro.OrigemTipo.MANUAL, TituloFinanceiro.OrigemTipo.AJUSTE}", b)
        self.assertNotIn("origem_tipo != TituloFinanceiro.OrigemTipo.MANUAL", b)
