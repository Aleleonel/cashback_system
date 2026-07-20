from django.template.loader import get_template
from django.test import SimpleTestCase

from estoque import urls
from estoque.views import lista_movimentacoes


class EstoqueUIEstruturalTests(SimpleTestCase):
    def test_url_lista_movimentacoes_esta_registrada(self):
        padrao = next(
            item
            for item in urls.urlpatterns
            if item.name == 'lista_movimentacoes'
        )

        self.assertEqual(
            str(padrao.pattern),
            ''
        )
        self.assertIs(
            padrao.callback,
            lista_movimentacoes
        )

    def test_template_lista_movimentacoes_carrega(self):
        template = get_template(
            'estoque/movimentacoes/lista.html'
        )

        self.assertIsNotNone(template)

    def test_template_tabela_movimentacoes_carrega(self):
        template = get_template(
            'estoque/movimentacoes/_tabela_conteudo.html'
        )

        self.assertIsNotNone(template)