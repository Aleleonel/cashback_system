from django.test import SimpleTestCase
from django.urls import resolve, reverse

from produtos.views import (
    criar_categoria_view,
    criar_marca_view,
    criar_produto_view,
    criar_unidade_medida_view,
    detalhe_produto,
    editar_categoria_view,
    editar_marca_view,
    editar_produto_view,
    editar_unidade_medida_view,
    lista_categorias,
    lista_marcas,
    lista_produtos,
    lista_unidades_medida,
)


class ProdutosUrlsTestCase(SimpleTestCase):
    def test_url_lista_produtos(self):
        url = reverse(
            'produtos:lista_produtos'
        )

        self.assertEqual(
            resolve(url).func,
            lista_produtos
        )

    def test_url_criar_produto(self):
        url = reverse(
            'produtos:criar_produto'
        )

        self.assertEqual(
            resolve(url).func,
            criar_produto_view
        )

    def test_url_detalhe_produto(self):
        url = reverse(
            'produtos:detalhe_produto',
            args=[1]
        )

        self.assertEqual(
            resolve(url).func,
            detalhe_produto
        )

    def test_url_editar_produto(self):
        url = reverse(
            'produtos:editar_produto',
            args=[1]
        )

        self.assertEqual(
            resolve(url).func,
            editar_produto_view
        )

    def test_url_lista_categorias(self):
        url = reverse(
            'produtos:lista_categorias'
        )

        self.assertEqual(
            resolve(url).func,
            lista_categorias
        )

    def test_url_criar_categoria(self):
        url = reverse(
            'produtos:criar_categoria'
        )

        self.assertEqual(
            resolve(url).func,
            criar_categoria_view
        )

    def test_url_editar_categoria(self):
        url = reverse(
            'produtos:editar_categoria',
            args=[1]
        )

        self.assertEqual(
            resolve(url).func,
            editar_categoria_view
        )

    def test_url_lista_marcas(self):
        url = reverse(
            'produtos:lista_marcas'
        )

        self.assertEqual(
            resolve(url).func,
            lista_marcas
        )

    def test_url_criar_marca(self):
        url = reverse(
            'produtos:criar_marca'
        )

        self.assertEqual(
            resolve(url).func,
            criar_marca_view
        )

    def test_url_editar_marca(self):
        url = reverse(
            'produtos:editar_marca',
            args=[1]
        )

        self.assertEqual(
            resolve(url).func,
            editar_marca_view
        )

    def test_url_lista_unidades_medida(self):
        url = reverse(
            'produtos:lista_unidades_medida'
        )

        self.assertEqual(
            resolve(url).func,
            lista_unidades_medida
        )

    def test_url_criar_unidade_medida(self):
        url = reverse(
            'produtos:criar_unidade_medida'
        )

        self.assertEqual(
            resolve(url).func,
            criar_unidade_medida_view
        )

    def test_url_editar_unidade_medida(self):
        url = reverse(
            'produtos:editar_unidade_medida',
            args=[1]
        )

        self.assertEqual(
            resolve(url).func,
            editar_unidade_medida_view
        )
