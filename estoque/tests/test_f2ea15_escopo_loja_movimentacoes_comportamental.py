from pathlib import Path
from django.test import SimpleTestCase

class F2EA15EscopoLojaMovimentacoesComportamentalTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.view = Path("estoque/views/movimentacoes.py").read_text(encoding="utf-8")
        cls.selector = Path("estoque/selectors/movimentacoes.py").read_text(encoding="utf-8")
        cls.template = Path("estoque/templates/estoque/movimentacoes/lista.html").read_text(encoding="utf-8")

    def test_operador_restringe_queryset_a_loja_operacional(self):
        self.assertIn("lojas = lojas_relacao.filter(pk=loja_operacional.pk)", self.view)
        self.assertIn("lojas=lojas", self.view)
        self.assertIn("movimentacoes.filter(loja__in=lojas)", self.selector)

    def test_querystring_loja_nao_altera_escopo_operador(self):
        self.assertIn("if pode_filtrar_loja and loja_id.isdigit():", self.view)
        self.assertIn("elif usuario_operacional:", self.view)
        self.assertIn("loja_id = ''", self.view)

    def test_administrativo_recebe_lojas_da_matriz(self):
        self.assertIn("lojas_relacao.model.objects.filter(", self.view)
        self.assertIn("matriz=matriz", self.view)
        self.assertIn("pode_filtrar_loja = not usuario_operacional", self.view)

    def test_template_operador_nao_expoe_select_cross_store(self):
        self.assertIn("{% if pode_filtrar_loja %}", self.template)
        self.assertIn("<select class=", self.template)
        self.assertIn("{{ loja_operacional.nome }}", self.template)
        self.assertIn("disabled", self.template)

    def test_paginacao_deriva_do_queryset_restrito(self):
        scope_pos = self.view.index("movimentacoes = get_movimentacoes(")
        paginator_pos = self.view.index("Paginator(movimentacoes, 25)")
        self.assertLess(scope_pos, paginator_pos)