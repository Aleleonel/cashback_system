from pathlib import Path
from django.test import SimpleTestCase


class AutorizacaoOperacionalBehaviorContractTests(SimpleTestCase):
    def test_sidebar_real_separa_operacional_de_cadastros_estruturais(self):
        texto = Path("templates/partials/sidebar.html").read_text(encoding="utf-8")
        self.assertIn("pode_lancar_despesa_financeiro", texto)
        self.assertIn("pode_gerenciar_financeiro", texto)
        self.assertIn("financeiro:lancamento_manual", texto)
        self.assertIn("financeiro:planos_conta", texto)
        self.assertIn("financeiro:centros_custo", texto)
        self.assertIn("financeiro:instituicoes_bancarias", texto)
        self.assertIn("financeiro:contas_financeiras", texto)

    def test_contexto_expoe_flags_financeiras_granulares(self):
        texto = Path("core/context_processors.py").read_text(encoding="utf-8")
        self.assertIn("pode_lancar_despesa_financeiro", texto)
        self.assertIn("pode_baixar_financeiro", texto)
        self.assertIn("pode_gerenciar_financeiro", texto)
        self.assertIn("PERMISSAO_FINANCEIRO_LANCAR_DESPESA", texto)
        self.assertIn("PERMISSAO_FINANCEIRO_BAIXAR", texto)
        self.assertIn("PERMISSAO_FINANCEIRO_GERENCIAR", texto)