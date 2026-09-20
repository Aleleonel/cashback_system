from pathlib import Path
from django.test import SimpleTestCase

from accounts.permissions import (
    PERMISSAO_FINANCEIRO_GERENCIAR,
    PERMISSAO_FINANCEIRO_VISUALIZAR,
    PERMISSOES_FINANCEIRO,
    get_permissoes_extras_disponiveis,
)


class AutorizacaoFinanceiraOperacionalContratoTests(SimpleTestCase):
    def test_catalogo_expoe_lancar_despesa_e_baixar(self):
        itens = {item["codigo"]: item for item in get_permissoes_extras_disponiveis()}
        self.assertIn("financeiro.lancar_despesa", itens)
        self.assertIn("financeiro.baixar", itens)
        self.assertEqual(itens["financeiro.lancar_despesa"]["grupo"], "Financeiro")
        self.assertEqual(itens["financeiro.baixar"]["grupo"], "Financeiro")

    def test_permissoes_financeiro_integral_inclui_operacionais(self):
        self.assertIn("financeiro.lancar_despesa", PERMISSOES_FINANCEIRO)
        self.assertIn("financeiro.baixar", PERMISSOES_FINANCEIRO)
        self.assertIn(PERMISSAO_FINANCEIRO_VISUALIZAR, PERMISSOES_FINANCEIRO)
        self.assertIn(PERMISSAO_FINANCEIRO_GERENCIAR, PERMISSOES_FINANCEIRO)

    def test_views_usam_permissoes_granulares(self):
        texto = Path("financeiro/views.py").read_text(encoding="utf-8")
        self.assertIn("PERMISSAO_FINANCEIRO_LANCAR_DESPESA", texto)
        self.assertIn("PERMISSAO_FINANCEIRO_BAIXAR", texto)
        self.assertRegex(texto, r"@require_permission\(PERMISSAO_FINANCEIRO_LANCAR_DESPESA\)\s+def\s+lancamento_manual")
        self.assertRegex(texto, r"@require_permission\(PERMISSAO_FINANCEIRO_BAIXAR\)\s+def\s+parcela_baixa_nova")

    def test_operador_padrao_nao_recebe_financeiro_automaticamente(self):
        from accounts.permissions import PERMISSOES_POR_PERFIL
        operador = PERMISSOES_POR_PERFIL["operador"]
        self.assertNotIn("financeiro.visualizar", operador)
        self.assertNotIn("financeiro.lancar_despesa", operador)
        self.assertNotIn("financeiro.baixar", operador)
        self.assertNotIn("financeiro.gerenciar", operador)