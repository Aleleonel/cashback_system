from pathlib import Path

from django.test import SimpleTestCase


class Pdv04E2HistoricoFechamentosContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.urls = Path("pdv/urls.py").read_text(encoding="utf-8")
        cls.template = Path(
            "pdv/templates/pdv/historico_fechamentos.html"
        ).read_text(encoding="utf-8")
        cls.sidebar = Path(
            "templates/partials/sidebar.html"
        ).read_text(encoding="utf-8")
        cls.inicio = Path(
            "pdv/templates/pdv/inicio.html"
        ).read_text(encoding="utf-8")

    def test_rota_nomeada_existe(self):
        self.assertIn('name="historico_fechamentos"', self.urls)
        self.assertIn("views.historico_fechamentos", self.urls)

    def test_view_e_protegida(self):
        self.assertIn(
            "@require_permission(PERMISSAO_PDV_FECHAR_CAIXA)",
            self.views,
        )
        self.assertIn("def historico_fechamentos(request):", self.views)

    def test_view_isola_matriz_e_lojas(self):
        self.assertIn("caixa__matriz=matriz", self.views)
        self.assertIn("caixa__loja__in=lojas", self.views)

    def test_filtros_e_paginacao_existem(self):
        for campo in (
            "data_inicio",
            "data_fim",
            "caixa",
            "operador",
            "status",
        ):
            self.assertIn(f'name="{campo}"', self.template)
        self.assertIn("Paginator(sessoes, 20)", self.views)
        self.assertIn("page_obj", self.template)

    def test_totais_existem(self):
        for campo in (
            "total_sessoes",
            "total_abertura",
            "total_calculado",
            "total_informado",
            "total_diferenca",
        ):
            self.assertIn(campo, self.views)
            self.assertIn(campo, self.template)

    def test_sidebar_tem_secao_caixa_sem_frente_duplicada(self):
        self.assertIn("PDV-04E.2 - SECAO CAIXA", self.sidebar)
        self.assertIn("Abrir Caixa", self.sidebar)
        self.assertIn("Fechar Caixa", self.sidebar)
        self.assertIn("Histórico de Fechamentos", self.sidebar)

        inicio_secao = self.sidebar.index(
            "PDV-04E.2 - SECAO CAIXA"
        )
        trecho_caixa = self.sidebar[inicio_secao:]
        self.assertNotIn("Frente de Caixa", trecho_caixa)

        self.assertEqual(
            self.sidebar.count("Frente de Caixa"),
            1,
        )

    def test_pdv_tem_acesso_ao_historico(self):
        self.assertIn("pdv:historico_fechamentos", self.inicio)
