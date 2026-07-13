from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from empresas.models import Matriz
from produtos.choices import StatusProduto
from produtos.models import Categoria, Marca, Produto, UnidadeMedida
from produtos.selectors import (
    get_categoria,
    get_categorias,
    get_marca,
    get_marcas,
    get_produto,
    get_produto_por_codigo,
    get_produtos,
    get_unidade_medida,
    get_unidades_medida,
)


class ProdutoSelectorsTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Principal'
        )

        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        self.categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey'
        )

        self.categoria_inativa = Categoria.objects.create(
            matriz=self.matriz,
            nome='Descontinuados',
            ativa=False
        )

        self.marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps'
        )

        self.marca_inativa = Marca.objects.create(
            matriz=self.matriz,
            nome='Marca Inativa',
            ativa=False
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade'
        )

        self.unidade_inativa = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='CX',
            descricao='Caixa',
            ativa=False
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            categoria=self.categoria,
            marca=self.marca,
            unidade_medida=self.unidade,
            codigo_interno='PROD-001',
            sku='SKU-001',
            gtin='7891234567890',
            ncm='21069030',
            nome='Whey Special Flavor',
            descricao='Whey sabor leite condensado',
            custo_base=Decimal('50.00'),
            preco_venda=Decimal('100.00')
        )

        self.produto_inativo = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='PROD-002',
            nome='Produto Inativo',
            custo_base=Decimal('20.00'),
            preco_venda=Decimal('40.00'),
            status=StatusProduto.INATIVO
        )

        unidade_outra_matriz = UnidadeMedida.objects.create(
            matriz=self.outra_matriz,
            sigla='UN',
            descricao='Unidade'
        )

        self.produto_outra_matriz = Produto.objects.create(
            matriz=self.outra_matriz,
            unidade_medida=unidade_outra_matriz,
            codigo_interno='PROD-001',
            nome='Produto Outra Matriz',
            custo_base=Decimal('10.00'),
            preco_venda=Decimal('20.00')
        )

    def test_lista_categorias_somente_da_matriz(self):
        categorias = get_categorias(
            matriz=self.matriz
        )

        self.assertEqual(
            list(categorias),
            [self.categoria_inativa, self.categoria]
        )

    def test_lista_somente_categorias_ativas(self):
        categorias = get_categorias(
            matriz=self.matriz,
            somente_ativas=True
        )

        self.assertEqual(
            list(categorias),
            [self.categoria]
        )

    def test_busca_categoria_por_nome(self):
        categorias = get_categorias(
            matriz=self.matriz,
            busca='whey'
        )

        self.assertEqual(
            list(categorias),
            [self.categoria]
        )

    def test_get_categoria_respeita_matriz(self):
        with self.assertRaises(ObjectDoesNotExist):
            get_categoria(
                matriz=self.outra_matriz,
                categoria_id=self.categoria.id
            )

    def test_lista_marcas_somente_ativas(self):
        marcas = get_marcas(
            matriz=self.matriz,
            somente_ativas=True
        )

        self.assertEqual(
            list(marcas),
            [self.marca]
        )

    def test_busca_marca(self):
        marcas = get_marcas(
            matriz=self.matriz,
            busca='corps'
        )

        self.assertEqual(
            list(marcas),
            [self.marca]
        )

    def test_get_marca_respeita_matriz(self):
        with self.assertRaises(ObjectDoesNotExist):
            get_marca(
                matriz=self.outra_matriz,
                marca_id=self.marca.id
            )

    def test_lista_unidades_somente_ativas(self):
        unidades = get_unidades_medida(
            matriz=self.matriz,
            somente_ativas=True
        )

        self.assertEqual(
            list(unidades),
            [self.unidade]
        )

    def test_busca_unidade_por_descricao(self):
        unidades = get_unidades_medida(
            matriz=self.matriz,
            busca='unidade'
        )

        self.assertEqual(
            list(unidades),
            [self.unidade]
        )

    def test_get_unidade_respeita_matriz(self):
        with self.assertRaises(ObjectDoesNotExist):
            get_unidade_medida(
                matriz=self.outra_matriz,
                unidade_id=self.unidade.id
            )

    def test_lista_produtos_somente_da_matriz(self):
        produtos = get_produtos(
            matriz=self.matriz
        )

        self.assertEqual(
            set(produtos),
            {
                self.produto,
                self.produto_inativo,
            }
        )

    def test_lista_somente_produtos_ativos(self):
        produtos = get_produtos(
            matriz=self.matriz,
            somente_ativos=True
        )

        self.assertEqual(
            list(produtos),
            [self.produto]
        )

    def test_filtra_produtos_por_categoria(self):
        produtos = get_produtos(
            matriz=self.matriz,
            categoria=self.categoria
        )

        self.assertEqual(
            list(produtos),
            [self.produto]
        )

    def test_filtra_produtos_por_marca(self):
        produtos = get_produtos(
            matriz=self.matriz,
            marca=self.marca
        )

        self.assertEqual(
            list(produtos),
            [self.produto]
        )

    def test_busca_produto_por_nome(self):
        produtos = get_produtos(
            matriz=self.matriz,
            busca='special'
        )

        self.assertEqual(
            list(produtos),
            [self.produto]
        )

    def test_busca_produto_por_codigo_interno(self):
        produto = get_produto_por_codigo(
            matriz=self.matriz,
            codigo='prod-001'
        )

        self.assertEqual(
            produto,
            self.produto
        )

    def test_busca_produto_por_sku(self):
        produto = get_produto_por_codigo(
            matriz=self.matriz,
            codigo='sku-001'
        )

        self.assertEqual(
            produto,
            self.produto
        )

    def test_busca_produto_por_gtin(self):
        produto = get_produto_por_codigo(
            matriz=self.matriz,
            codigo='7891234567890'
        )

        self.assertEqual(
            produto,
            self.produto
        )

    def test_busca_codigo_vazio_retorna_none(self):
        produto = get_produto_por_codigo(
            matriz=self.matriz,
            codigo=''
        )

        self.assertIsNone(produto)

    def test_get_produto_respeita_matriz(self):
        with self.assertRaises(ObjectDoesNotExist):
            get_produto(
                matriz=self.outra_matriz,
                produto_id=self.produto.id
            )
