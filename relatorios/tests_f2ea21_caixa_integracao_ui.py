from django.test import SimpleTestCase
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class F2EA21CaixaIntegracaoUIContratoTests(SimpleTestCase):
    def text(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_relatorios_expoe_hub_caixa_com_permissao_relatorios(self):
        urls=self.text("relatorios/urls.py")
        views=self.text("relatorios/views.py")
        self.assertIn("hub_caixa", urls)
        self.assertIn("name='caixa'", urls)
        self.assertIn("def hub_caixa", views)
        bloco=views[views.index("def hub_caixa")-180:views.index("def hub_caixa")+300]
        self.assertIn("PERMISSAO_RELATORIOS_DASHBOARD", bloco)

    def test_hub_caixa_aponta_para_historico_em_modo_relatorio(self):
        tpl=self.text("relatorios/templates/relatorios/caixa.html")
        self.assertIn("pdv:historico_fechamentos", tpl)
        self.assertIn("modo_relatorio=1", tpl)

    def test_historico_tem_acao_para_demonstrativo(self):
        tpl=self.text("pdv/templates/pdv/historico_fechamentos.html")
        self.assertIn("pdv:demonstrativo_caixa", tpl)
        self.assertIn("Demonstrativo", tpl)

    def test_historico_suporta_modo_relatorio_sem_quebrar_permissao_pdv(self):
        views=self.text("pdv/views.py")
        inicio=views.index("def historico_fechamentos")
        fim=views.index("# F2EA21 - DEMONSTRATIVO", inicio)
        bloco=views[inicio:fim]
        self.assertIn("modo_relatorio", bloco)
        self.assertIn("PERMISSAO_RELATORIOS_DASHBOARD", bloco)
        self.assertIn("PERMISSAO_PDV_FECHAR_CAIXA", bloco)
        self.assertIn("usuario_tem_permissao(", bloco)

    def test_historico_relatorio_aplica_escopo_global_loja(self):
        views=self.text("pdv/views.py")
        inicio=views.index("def historico_fechamentos")
        fim=views.index("# F2EA21 - DEMONSTRATIVO", inicio)
        bloco=views[inicio:fim]
        self.assertIn("loja_operacional_id", bloco)
        self.assertIn("usuario_operacional", bloco)
        self.assertIn("Loja.objects.filter(matriz=matriz)", bloco)
        self.assertIn('request.GET.get("loja")', bloco)

    def test_sidebar_financeiro_nao_usa_estoque_como_estado_ativo(self):
        base=self.text("templates/partials/sidebar.html")
        inicio=base.index("{% url 'relatorios:financeiro' %}")
        fim=base.index("</a>", inicio)
        bloco=base[inicio:fim]
        self.assertNotIn("url_name == 'estoque'", bloco)
        self.assertNotIn('url_name == "estoque"', bloco)
        self.assertIn("url_name == 'financeiro'", bloco)

    def test_sidebar_expoe_caixa_em_relatorios(self):
        base=self.text("templates/partials/sidebar.html")
        self.assertIn("relatorios:caixa", base)
        self.assertIn("Caixa", base)
