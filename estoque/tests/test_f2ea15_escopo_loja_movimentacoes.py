from pathlib import Path
from django.test import SimpleTestCase

class F2EA15EscopoLojaMovimentacoesContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.view = Path("estoque/views/movimentacoes.py").read_text(encoding="utf-8")
        cls.selector = Path("estoque/selectors/movimentacoes.py").read_text(encoding="utf-8")
        cls.template = Path("estoque/templates/estoque/movimentacoes/lista.html").read_text(encoding="utf-8")

    def test_view_distingue_operador_de_administrativo(self):
        self.assertIn("PERFIL_OPERADOR", self.view)
        self.assertIn("usuario_operacional", self.view)
        self.assertIn("pode_filtrar_loja", self.view)

    def test_operador_usa_loja_operacional_da_sessao(self):
        self.assertIn("loja_operacional_id", self.view)
        self.assertIn("request.session", self.view)

    def test_selector_aceita_escopo_de_loja(self):
        self.assertIn("lojas", self.selector)
        self.assertIn("loja__in", self.selector)

    def test_filtro_loja_so_e_aplicado_quando_permitido(self):
        self.assertIn("pode_filtrar_loja", self.view)
        self.assertIn("request.GET.get", self.view)
        self.assertIn("loja", self.view)

    def test_template_condiciona_filtro_loja_por_perfil(self):
        self.assertIn("pode_filtrar_loja", self.template)
        self.assertIn("loja_operacional", self.template)