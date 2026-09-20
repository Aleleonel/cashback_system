from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[1]


class FinanceiroUiOperacionalR9HardeningTests(SimpleTestCase):
    def test_documento_referencia_respeita_limite_do_modelo(self):
        source = (ROOT / "financeiro" / "forms.py").read_text(encoding="utf-8")
        self.assertIn('documento_referencia = forms.CharField(max_length=100', source)
        self.assertNotIn('documento_referencia = forms.CharField(max_length=120', source)

    def test_sidebar_expoe_todos_cadastros_mestres_financeiros(self):
        source = (ROOT / "templates" / "partials" / "sidebar.html").read_text(encoding="utf-8")
        self.assertIn("financeiro:planos_conta", source)
        self.assertIn("financeiro:centros_custo", source)
        self.assertIn("financeiro:instituicoes_bancarias", source)
        self.assertIn("financeiro:contas_financeiras", source)

    def test_idempotencia_manual_nao_e_derivada_do_payload_financeiro(self):
        source = (ROOT / "financeiro" / "views.py").read_text(encoding="utf-8")
        self.assertNotIn('f"manual:{matriz.pk}:{request.user.pk}:"', source)
        self.assertIn("chave_idempotencia", source)