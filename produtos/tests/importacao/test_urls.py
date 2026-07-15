from django.test import SimpleTestCase
from django.urls import resolve, reverse

from produtos.views import (
    baixar_modelo_importacao_produtos,
    confirmar_importacao_produtos,
    importar_produtos_view,
)


class ImportacaoProdutosUrlsTestCase(SimpleTestCase):
    def test_url_importar_produtos(self):
        url = reverse(
            'produtos:importar_produtos'
        )

        self.assertEqual(
            resolve(url).func,
            importar_produtos_view
        )

    def test_url_baixar_modelo(self):
        url = reverse(
            'produtos:baixar_modelo_importacao'
        )

        self.assertEqual(
            resolve(url).func,
            baixar_modelo_importacao_produtos
        )

    def test_url_confirmar_importacao(self):
        url = reverse(
            'produtos:confirmar_importacao'
        )

        funcao = resolve(url).func

        self.assertEqual(
            funcao,
            confirmar_importacao_produtos
        )
