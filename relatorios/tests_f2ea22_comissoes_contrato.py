from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[1]


class F2EA22ComissoesContratoTests(SimpleTestCase):
    def text(self, relative_path):
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_relatorios_expoe_rota_comissoes(self):
        urls = self.text("relatorios/urls.py")
        self.assertIn("hub_comissoes", urls)
        self.assertIn("name='comissoes'", urls)

    def test_view_comissoes_usa_permissao_relatorios(self):
        views = self.text("relatorios/views.py")
        self.assertIn("def hub_comissoes", views)
        inicio = views.index("def hub_comissoes")
        bloco = views[max(0, inicio - 220):inicio + 500]
        self.assertIn("PERMISSAO_RELATORIOS_DASHBOARD", bloco)

    def test_relatorio_comissoes_tem_view_read_only_propria(self):
        views = self.text("relatorios/views.py")
        self.assertIn("def relatorio_comissoes", views)
        inicio = views.index("def relatorio_comissoes")
        bloco = views[max(0, inicio - 220):inicio + 2600]
        self.assertIn("PERMISSAO_RELATORIOS_DASHBOARD", bloco)
        self.assertNotIn("fechar_comissoes_competencia(", bloco)

    def test_relatorio_consulta_snapshots_persistidos(self):
        views = self.text("relatorios/views.py")
        inicio = views.index("def _dados_relatorio_comissoes")
        fim = views.index("def relatorio_comissoes", inicio)
        bloco = views[inicio:fim]
        self.assertIn("FechamentoComissao", bloco)
        self.assertIn("ComissaoVendedor", bloco)

    def test_relatorio_isola_matriz(self):
        views = self.text("relatorios/views.py")
        inicio = views.index("def _dados_relatorio_comissoes")
        fim = views.index("def relatorio_comissoes", inicio)
        bloco = views[inicio:fim]
        self.assertIn("matriz", bloco)
        self.assertTrue(
            "matriz=matriz" in bloco or "matriz_id" in bloco,
            "Relatorio deve filtrar snapshots pela matriz autenticada.",
        )

    def test_operador_fica_na_loja_operacional(self):
        views = self.text("relatorios/views.py")
        inicio = views.index("def _dados_relatorio_comissoes")
        fim = views.index("def relatorio_comissoes", inicio)
        bloco = views[inicio:fim]
        self.assertIn("PERFIL_OPERADOR", bloco)
        self.assertIn("loja_operacional_id", bloco)
        self.assertIn("request.user.lojas", bloco)

    def test_administrativo_pode_filtrar_loja_da_propria_matriz(self):
        views = self.text("relatorios/views.py")
        inicio = views.index("def _dados_relatorio_comissoes")
        fim = views.index("def relatorio_comissoes", inicio)
        bloco = views[inicio:fim]
        self.assertIn('request.GET.get("loja")', bloco)
        self.assertIn("Loja.objects.filter(matriz=matriz)", bloco)

    def test_template_hub_comissoes_existe(self):
        template = ROOT / "relatorios/templates/relatorios/comissoes.html"
        self.assertTrue(template.exists())
        texto = template.read_text(encoding="utf-8")
        self.assertIn("relatorios:relatorio_comissoes", texto)
        self.assertIn("relatorio_comissoes", texto)

    def test_template_relatorio_comissoes_existe_e_expoe_snapshots(self):
        template = ROOT / "relatorios/templates/relatorios/relatorio_comissoes.html"
        self.assertTrue(template.exists())
        texto = template.read_text(encoding="utf-8")
        for termo in [
            "Total vendido",
            "Percentual",
            "Vendedor",
            "Elegibilidade",
            "item.fechamento.total_vendas_loja",
            "item.vendedor_nome_original",
            "item.total_vendas_vendedor",
            "item.valor_comissao",
        ]:
            self.assertIn(termo, texto)

    def test_hub_principal_expoe_comissoes(self):
        views = self.text("relatorios/views.py")
        urls = self.text("relatorios/urls.py")
        self.assertIn("hub_comissoes", views)
        self.assertIn("comissoes", urls)
