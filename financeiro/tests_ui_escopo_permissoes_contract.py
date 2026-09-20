from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parent.parent


class FinanceiroUiEscopoPermissoesContractTests(SimpleTestCase):
    def _read(self, relative_path):
        path = ROOT / relative_path
        self.assertTrue(path.exists(), f"Arquivo esperado ausente: {relative_path}")
        return path.read_text(encoding="utf-8")

    def test_financeiro_tem_urls_views_e_template_painel(self):
        self.assertTrue((ROOT / "financeiro" / "urls.py").exists())
        self.assertTrue((ROOT / "financeiro" / "views.py").exists())
        self.assertTrue(
            (ROOT / "financeiro" / "templates" / "financeiro" / "painel.html").exists()
        )

    def test_config_inclui_namespace_financeiro(self):
        source = self._read("config/urls.py")
        self.assertIn("include('financeiro.urls')", source)
        self.assertIn("'financeiro/'", source)

    def test_financeiro_urls_expoem_painel_listagem_e_detalhe(self):
        source = self._read("financeiro/urls.py")
        self.assertIn("app_name = 'financeiro'", source)
        self.assertIn('name="painel"', source.replace("'", '"'))
        self.assertIn('name="titulos"', source.replace("'", '"'))
        self.assertIn('name="titulo_detalhe"', source.replace("'", '"'))

    def test_sidebar_financeiro_fica_entre_compras_e_fiscal(self):
        source = self._read("templates/partials/sidebar.html")
        compras = source.index("UI-COMPRAS-FIM")
        financeiro = source.index('data-sidebar-section="financeiro"')
        fiscal = source.index('data-sidebar-section="fiscal"')
        self.assertLess(compras, financeiro)
        self.assertLess(financeiro, fiscal)
        self.assertIn("{% if pode_ver_financeiro %}", source)
        self.assertIn("Financeiro", source)
        self.assertIn("bi-cash-stack", source)

    def test_permissoes_financeiro_usam_accounts_existente(self):
        source = self._read("accounts/permissions.py")
        self.assertIn("PERMISSAO_FINANCEIRO_VISUALIZAR", source)
        self.assertIn("PERMISSAO_FINANCEIRO_GERENCIAR", source)

    def test_context_processor_expoe_permissao_sidebar_financeiro(self):
        source = self._read("core/context_processors.py")
        self.assertIn("PERMISSAO_FINANCEIRO_VISUALIZAR", source)
        self.assertIn("'pode_ver_financeiro'", source)

    def test_selectors_tem_escopo_explicito_sem_ambiguidade_loja_none(self):
        source = self._read("financeiro/selectors.py")
        self.assertIn("ESCOPO_CONSOLIDADO", source)
        self.assertIn("ESCOPO_MATRIZ", source)
        self.assertIn("ESCOPO_LOJA", source)
        self.assertIn("escopo=", source)
        self.assertIn("loja__isnull=True", source)

    def test_views_revalidam_matriz_loja_e_permissao_no_backend(self):
        source = self._read("financeiro/views.py")
        self.assertIn("PERMISSAO_FINANCEIRO_VISUALIZAR", source)
        self.assertIn("request.user", source)
        self.assertIn("matriz", source)
        self.assertIn("loja", source)

    def test_painel_exibe_cards_filtros_e_listagem(self):
        source = self._read("financeiro/templates/financeiro/painel.html")
        self.assertIn("Contas a receber", source)
        self.assertIn("Contas a pagar", source)
        self.assertIn("Saldo", source)
        self.assertIn("Consolidado", source)
        self.assertIn("Somente matriz", source)
        self.assertIn("Loja", source)
        self.assertIn("Títulos", source)

    def test_detalhe_titulo_e_read_only_com_parcelas_e_baixas(self):
        source = self._read("financeiro/templates/financeiro/titulo_detalhe.html")
        self.assertIn("Parcelas", source)
        self.assertIn("Baixas", source)
        self.assertNotIn("<form", source.lower())
        self.assertNotIn("Excluir", source)