from pathlib import Path
from django.test import SimpleTestCase


class LancarDespesaNaturezaContratoTests(SimpleTestCase):
    def test_view_forca_pagar_para_permissao_operacional(self):
        texto = Path("financeiro/views.py").read_text(encoding="utf-8")
        self.assertIn("PERMISSAO_FINANCEIRO_LANCAR_DESPESA", texto)
        self.assertIn("PERMISSAO_FINANCEIRO_GERENCIAR", texto)
        self.assertRegex(
            texto,
            r"usuario_tem_permissao\(\s*request\.user,\s*PERMISSAO_FINANCEIRO_GERENCIAR\s*\)",
        )
        self.assertRegex(
            texto,
            r"dados\[\s*[\"']natureza[\"']\s*\]\s*=\s*TituloFinanceiro\.Natureza\.PAGAR",
        )

    def test_formulario_operacional_nao_deve_expor_receber_livremente(self):
        texto = Path("financeiro/views.py").read_text(encoding="utf-8")
        self.assertRegex(
            texto,
            r"form\.fields\[\s*[\"']natureza[\"']\s*\]",
        )
        self.assertIn("TituloFinanceiro.Natureza.PAGAR", texto)