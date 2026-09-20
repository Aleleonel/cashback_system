from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parent.parent


class FinanceiroUiOperacionalR9ContractTests(SimpleTestCase):
    """Contrato RED da UI operacional financeira R9.

    Estes testes sao deliberadamente estruturais. Eles congelam a fronteira
    esperada antes da implementacao sem acessar banco real.
    """

    def _read(self, relative_path):
        path = ROOT / relative_path
        self.assertTrue(path.exists(), f"Arquivo esperado ausente: {relative_path}")
        return path.read_text(encoding="utf-8")

    def test_forms_financeiro_existe_com_cadastros_e_lancamento_manual(self):
        source = self._read("financeiro/forms.py")
        for nome in (
            "PlanoContaForm",
            "CentroCustoForm",
            "InstituicaoBancariaForm",
            "ContaFinanceiraForm",
            "LancamentoManualForm",
        ):
            self.assertIn(f"class {nome}", source)

    def test_urls_preservam_consultas_e_expoem_cadastros_mestres(self):
        source = self._read("financeiro/urls.py")
        for nome in (
            'name="painel"',
            'name="titulos"',
            'name="titulo_detalhe"',
            'name="planos_conta"',
            'name="plano_conta_novo"',
            'name="centros_custo"',
            'name="centro_custo_novo"',
            'name="instituicoes_bancarias"',
            'name="instituicao_bancaria_nova"',
            'name="contas_financeiras"',
            'name="conta_financeira_nova"',
        ):
            self.assertIn(nome, source.replace("'", '"'))

    def test_urls_expoem_lancamento_manual(self):
        source = self._read("financeiro/urls.py")
        self.assertIn('name="lancamento_manual"', source.replace("'", '"'))

    def test_views_mutaveis_usam_permissao_gerenciar(self):
        source = self._read("financeiro/views.py")
        self.assertIn("PERMISSAO_FINANCEIRO_GERENCIAR", source)
        self.assertGreaterEqual(
            source.count("@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)"),
            5,
        )

    def test_lancamento_manual_delega_ao_service_existente(self):
        source = self._read("financeiro/views.py")
        self.assertIn("criar_lancamento_manual", source)
        self.assertIn("LancamentoManualForm", source)

    def test_templates_cadastros_e_lancamento_manual_existem(self):
        esperados = (
            "financeiro/templates/financeiro/planos_conta.html",
            "financeiro/templates/financeiro/plano_conta_form.html",
            "financeiro/templates/financeiro/centros_custo.html",
            "financeiro/templates/financeiro/centro_custo_form.html",
            "financeiro/templates/financeiro/instituicoes_bancarias.html",
            "financeiro/templates/financeiro/instituicao_bancaria_form.html",
            "financeiro/templates/financeiro/contas_financeiras.html",
            "financeiro/templates/financeiro/conta_financeira_form.html",
            "financeiro/templates/financeiro/lancamento_manual.html",
        )
        for relative_path in esperados:
            self.assertTrue(
                (ROOT / relative_path).exists(),
                f"Template operacional esperado ausente: {relative_path}",
            )

    def test_sidebar_preserva_consultas_e_expoe_entrada_operacional(self):
        source = self._read("templates/partials/sidebar.html")
        self.assertIn("financeiro:painel", source)
        self.assertIn("financeiro:titulos", source)
        self.assertIn("financeiro:lancamento_manual", source)
        self.assertIn("financeiro:planos_conta", source)