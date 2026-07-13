from decimal import Decimal

from django.test import TestCase

from empresas.models import Matriz
from produtos.forms import (
    CategoriaForm,
    MarcaForm,
    ProdutoForm,
    UnidadeMedidaForm,
)
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)


class ProdutoFormsTestCase(TestCase):
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
            nome='Categoria Inativa',
            ativa=False
        )

        self.categoria_outra_matriz = (
            Categoria.objects.create(
                matriz=self.outra_matriz,
                nome='Outra Categoria'
            )
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

        self.marca_outra_matriz = Marca.objects.create(
            matriz=self.outra_matriz,
            nome='Outra Marca'
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

        self.unidade_outra_matriz = (
            UnidadeMedida.objects.create(
                matriz=self.outra_matriz,
                sigla='UN',
                descricao='Unidade'
            )
        )

    def dados_produto(self, **alteracoes):
        dados = {
            'categoria': str(self.categoria.id),
            'marca': str(self.marca.id),
            'unidade_medida': str(self.unidade.id),
            'codigo_interno': ' prod-001 ',
            'sku': ' sku-001 ',
            'gtin': '789.123.456.789-0',
            'ncm': '2106.90.30',
            'nome': ' Whey Special Flavor ',
            'descricao': ' Produto de teste ',
            'custo_base': '50.00',
            'preco_venda': '100.00',
            'peso_liquido_gramas': '840',
            'peso_bruto_gramas': '950',
            'altura_cm': '25.00',
            'largura_cm': '15.00',
            'comprimento_cm': '15.00',
            'controla_estoque': 'on',
            'estoque_minimo': '5.000',
            'status': 'ativo',
        }

        dados.update(alteracoes)

        return dados

    def test_forms_usam_classes_bootstrap(self):
        forms = [
            CategoriaForm(),
            MarcaForm(),
            UnidadeMedidaForm(),
            ProdutoForm(matriz=self.matriz),
        ]

        for form in forms:
            for campo in form.fields.values():
                self.assertTrue(
                    campo.widget.attrs.get('class')
                )

    def test_categoria_form_normaliza_campos(self):
        form = CategoriaForm(data={
            'nome': ' Whey ',
            'descricao': ' Categoria de whey ',
            'ativa': 'on',
        })

        self.assertTrue(
            form.is_valid(),
            form.errors
        )
        self.assertEqual(
            form.cleaned_data['nome'],
            'Whey'
        )
        self.assertEqual(
            form.cleaned_data['descricao'],
            'Categoria de whey'
        )

    def test_marca_form_normaliza_campos(self):
        form = MarcaForm(data={
            'nome': ' Pro Corps ',
            'fabricante': ' Fabricante ',
            'ativa': 'on',
        })

        self.assertTrue(
            form.is_valid(),
            form.errors
        )
        self.assertEqual(
            form.cleaned_data['nome'],
            'Pro Corps'
        )
        self.assertEqual(
            form.cleaned_data['fabricante'],
            'Fabricante'
        )

    def test_unidade_form_normaliza_sigla(self):
        form = UnidadeMedidaForm(data={
            'sigla': ' un ',
            'descricao': ' Unidade ',
            'ativa': 'on',
        })

        self.assertTrue(
            form.is_valid(),
            form.errors
        )
        self.assertEqual(
            form.cleaned_data['sigla'],
            'UN'
        )
        self.assertEqual(
            form.cleaned_data['descricao'],
            'Unidade'
        )

    def test_produto_form_filtra_relacionamentos_por_matriz(self):
        form = ProdutoForm(
            matriz=self.matriz
        )

        self.assertIn(
            self.categoria,
            form.fields['categoria'].queryset
        )
        self.assertNotIn(
            self.categoria_outra_matriz,
            form.fields['categoria'].queryset
        )

        self.assertIn(
            self.marca,
            form.fields['marca'].queryset
        )
        self.assertNotIn(
            self.marca_outra_matriz,
            form.fields['marca'].queryset
        )

        self.assertIn(
            self.unidade,
            form.fields['unidade_medida'].queryset
        )
        self.assertNotIn(
            self.unidade_outra_matriz,
            form.fields['unidade_medida'].queryset
        )

    def test_produto_form_exibe_somente_relacionamentos_ativos(self):
        form = ProdutoForm(
            matriz=self.matriz
        )

        self.assertNotIn(
            self.categoria_inativa,
            form.fields['categoria'].queryset
        )
        self.assertNotIn(
            self.marca_inativa,
            form.fields['marca'].queryset
        )
        self.assertNotIn(
            self.unidade_inativa,
            form.fields['unidade_medida'].queryset
        )

    def test_edicao_preserva_relacionamentos_inativos_atuais(self):
        produto = Produto.objects.create(
            matriz=self.matriz,
            categoria=self.categoria_inativa,
            marca=self.marca_inativa,
            unidade_medida=self.unidade_inativa,
            codigo_interno='PROD-001',
            nome='Produto',
            custo_base=Decimal('10.00'),
            preco_venda=Decimal('20.00'),
        )

        form = ProdutoForm(
            instance=produto,
            matriz=self.matriz
        )

        self.assertIn(
            self.categoria_inativa,
            form.fields['categoria'].queryset
        )
        self.assertIn(
            self.marca_inativa,
            form.fields['marca'].queryset
        )
        self.assertIn(
            self.unidade_inativa,
            form.fields['unidade_medida'].queryset
        )

    def test_produto_form_normaliza_identificacao(self):
        form = ProdutoForm(
            data=self.dados_produto(),
            matriz=self.matriz
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )
        self.assertEqual(
            form.cleaned_data['codigo_interno'],
            'PROD-001'
        )
        self.assertEqual(
            form.cleaned_data['sku'],
            'SKU-001'
        )
        self.assertEqual(
            form.cleaned_data['gtin'],
            '7891234567890'
        )
        self.assertEqual(
            form.cleaned_data['ncm'],
            '21069030'
        )
        self.assertEqual(
            form.cleaned_data['nome'],
            'Whey Special Flavor'
        )

    def test_produto_form_impede_peso_bruto_menor(self):
        form = ProdutoForm(
            data=self.dados_produto(
                peso_liquido_gramas='900',
                peso_bruto_gramas='850',
            ),
            matriz=self.matriz
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'peso_bruto_gramas',
            form.errors
        )

    def test_produto_form_sem_matriz_nao_expoe_relacionamentos(self):
        form = ProdutoForm()

        self.assertFalse(
            form.fields['categoria'].queryset.exists()
        )
        self.assertFalse(
            form.fields['marca'].queryset.exists()
        )
        self.assertFalse(
            form.fields['unidade_medida'].queryset.exists()
        )

    def test_form_nao_expoe_origem_preco(self):
        form = ProdutoForm(
            matriz=self.matriz
        )

        self.assertNotIn(
            'origem_preco',
            form.fields
        )
