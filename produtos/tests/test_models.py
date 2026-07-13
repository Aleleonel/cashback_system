from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from produtos.choices import OrigemPreco, StatusProduto
from produtos.models import Categoria, Marca, Produto, UnidadeMedida


class ProdutoModelTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Principal'
        )

        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz'
        )

        self.categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Whey Protein'
        )

        self.marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Pro Corps',
            fabricante='Pro Corps'
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='un',
            descricao='Unidade'
        )

    def criar_produto(self, **dados):
        valores = {
            'matriz': self.matriz,
            'categoria': self.categoria,
            'marca': self.marca,
            'unidade_medida': self.unidade,
            'codigo_interno': 'PROD-001',
            'sku': 'SKU-001',
            'gtin': '7891234567890',
            'ncm': '21069030',
            'nome': 'Whey Special Flavor',
            'custo_base': Decimal('50.00'),
            'preco_venda': Decimal('100.00'),
            'origem_preco': OrigemPreco.MANUAL,
            'peso_liquido_gramas': 840,
            'peso_bruto_gramas': 950,
            'altura_cm': Decimal('25.00'),
            'largura_cm': Decimal('15.00'),
            'comprimento_cm': Decimal('15.00'),
            'controla_estoque': True,
            'estoque_minimo': Decimal('5.000'),
            'status': StatusProduto.ATIVO,
        }

        valores.update(dados)

        return Produto.objects.create(**valores)

    def test_unidade_medida_normaliza_sigla(self):
        self.assertEqual(
            self.unidade.sigla,
            'UN'
        )

    def test_produto_normaliza_campos_de_identificacao(self):
        produto = self.criar_produto(
            codigo_interno=' prod-002 ',
            sku=' sku-002 ',
            gtin='789.123.456.789-0',
            ncm='2106.90.30',
            nome='  Whey 4  '
        )

        self.assertEqual(
            produto.codigo_interno,
            'PROD-002'
        )
        self.assertEqual(
            produto.sku,
            'SKU-002'
        )
        self.assertEqual(
            produto.gtin,
            '7891234567890'
        )
        self.assertEqual(
            produto.ncm,
            '21069030'
        )
        self.assertEqual(
            produto.nome,
            'Whey 4'
        )

    def test_calcula_lucro_bruto_unitario(self):
        produto = self.criar_produto()

        self.assertEqual(
            produto.lucro_bruto_unitario,
            Decimal('50.00')
        )

    def test_calcula_markup_percentual(self):
        produto = self.criar_produto()

        self.assertEqual(
            produto.markup_percentual,
            Decimal('100')
        )

    def test_calcula_margem_bruta_percentual(self):
        produto = self.criar_produto()

        self.assertEqual(
            produto.margem_bruta_percentual,
            Decimal('50')
        )

    def test_markup_retorna_none_quando_custo_for_zero(self):
        produto = self.criar_produto(
            custo_base=Decimal('0.00')
        )

        self.assertIsNone(
            produto.markup_percentual
        )

    def test_margem_retorna_none_quando_preco_for_zero(self):
        produto = self.criar_produto(
            custo_base=Decimal('0.00'),
            preco_venda=Decimal('0.00')
        )

        self.assertIsNone(
            produto.margem_bruta_percentual
        )

    def test_impede_peso_bruto_menor_que_peso_liquido(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_produto(
                peso_liquido_gramas=900,
                peso_bruto_gramas=850
            )

        self.assertIn(
            'peso_bruto_gramas',
            contexto.exception.message_dict
        )

    def test_impede_categoria_de_outra_matriz(self):
        categoria_outra_matriz = Categoria.objects.create(
            matriz=self.outra_matriz,
            nome='Creatina'
        )

        with self.assertRaises(ValidationError) as contexto:
            self.criar_produto(
                categoria=categoria_outra_matriz
            )

        self.assertIn(
            'categoria',
            contexto.exception.message_dict
        )

    def test_impede_marca_de_outra_matriz(self):
        marca_outra_matriz = Marca.objects.create(
            matriz=self.outra_matriz,
            nome='Outra Marca'
        )

        with self.assertRaises(ValidationError) as contexto:
            self.criar_produto(
                marca=marca_outra_matriz
            )

        self.assertIn(
            'marca',
            contexto.exception.message_dict
        )

    def test_impede_unidade_de_outra_matriz(self):
        unidade_outra_matriz = UnidadeMedida.objects.create(
            matriz=self.outra_matriz,
            sigla='CX',
            descricao='Caixa'
        )

        with self.assertRaises(ValidationError) as contexto:
            self.criar_produto(
                unidade_medida=unidade_outra_matriz
            )

        self.assertIn(
            'unidade_medida',
            contexto.exception.message_dict
        )

    def test_impede_codigo_interno_duplicado_na_mesma_matriz(self):
        self.criar_produto()

        with self.assertRaises(ValidationError):
            self.criar_produto(
                sku='SKU-002',
                gtin='7891234567891'
            )

    def test_permite_codigo_interno_igual_em_matrizes_diferentes(self):
        unidade_outra_matriz = UnidadeMedida.objects.create(
            matriz=self.outra_matriz,
            sigla='UN',
            descricao='Unidade'
        )

        primeiro = self.criar_produto()

        segundo = Produto.objects.create(
            matriz=self.outra_matriz,
            unidade_medida=unidade_outra_matriz,
            codigo_interno='PROD-001',
            nome='Produto da outra matriz',
            custo_base=Decimal('10.00'),
            preco_venda=Decimal('20.00')
        )

        self.assertNotEqual(
            primeiro.matriz_id,
            segundo.matriz_id
        )

    def test_impede_sku_duplicado_na_mesma_matriz(self):
        self.criar_produto()

        with self.assertRaises(ValidationError):
            self.criar_produto(
                codigo_interno='PROD-002',
                gtin='7891234567891'
            )

    def test_impede_gtin_duplicado_na_mesma_matriz(self):
        self.criar_produto()

        with self.assertRaises(ValidationError):
            self.criar_produto(
                codigo_interno='PROD-002',
                sku='SKU-002'
            )

    def test_permite_produtos_sem_sku_e_sem_gtin(self):
        primeiro = self.criar_produto(
            sku='',
            gtin=''
        )

        segundo = self.criar_produto(
            codigo_interno='PROD-002',
            sku='',
            gtin=''
        )

        self.assertEqual(
            primeiro.sku,
            ''
        )
        self.assertEqual(
            segundo.gtin,
            ''
        )
