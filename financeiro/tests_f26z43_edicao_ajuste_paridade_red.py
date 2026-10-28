from django.test import SimpleTestCase
from pathlib import Path

class F26Z43EdicaoAjusteParidadeTests(SimpleTestCase):
    def test_service_aceita_manual_e_ajuste(self):
        x=Path("financeiro/services.py").read_text(encoding="utf-8")
        b=x[x.index("def atualizar_lancamento_manual("):x.index("def cancelar_titulo_financeiro(")]
        self.assertIn("OrigemTipo.MANUAL",b)
        self.assertIn("OrigemTipo.AJUSTE",b)
        self.assertIn("origem_tipo not in",b)

    def test_detalhe_expoe_edicao_para_manual_e_ajuste(self):
        x=Path("financeiro/views.py").read_text(encoding="utf-8")
        linha=next(z for z in x.splitlines() if '"pode_editar_titulo"' in z)
        self.assertIn("OrigemTipo.MANUAL",linha)
        self.assertIn("OrigemTipo.AJUSTE",linha)
        self.assertIn("origem_tipo in",linha)
