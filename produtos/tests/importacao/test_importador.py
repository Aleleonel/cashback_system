from io import BytesIO

import pandas as pd
from django.template.loader import get_template
from django.test import TestCase
from openpyxl import load_workbook

from empresas.models import Matriz
from produtos.importacao import (
    gerar_modelo_importacao_produtos,
    validar_planilha_produtos,
)
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)


COLUNAS = [
    'Código Interno',
    'Nome',
    'SKU',
    'GTIN',
    'NCM',
    'Categoria',
    'Marca',
    'Unidade',
    'Custo Base',
    'Preço Venda',
    'Origem Preço',
    'Peso Líquido Gramas',
    'Peso Bruto Gramas',
    'Altura CM',
    'Largura CM',
    'Comprimento CM',
    'Controla Estoque',
    'Estoque Mínimo',
    'Status',
    'Descrição',
]


def criar_planilha(
    linhas,
    *,
    colunas=None,
):
    dataframe = pd.DataFrame(
        linhas,
        columns=colunas or COLUNAS,
    )

    arquivo = BytesIO()

    dataframe.to_excel(
        arquivo,
        index=False,
    )

    arquivo.seek(0)

    return arquivo


class ImportacaoProdutosTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Produtos'
        )

        self.categoria = Categoria.objects.create(
            matriz=self.matriz,
            nome='Suplementos',
            ativa=True,
        )

        self.marca = Marca.objects.create(
            matriz=self.matriz,
            nome='Marca Teste',
            ativa=True,
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
            ativa=True,
        )

    def linha_valida(
        self,
        *,
        codigo='PROD-001',
        nome='Produto Teste',
        sku='SKU-001',
        gtin='7891234567890',
    ):
        return [
            codigo,
            nome,
            sku,
            gtin,
            '21069030',
            self.categoria.nome,
            self.marca.nome,
            self.unidade.sigla,
            '50,00',
            '99,90',
            'Manual',
            '900',
            '1000',
            '25',
            '15',
            '15',
            'Sim',
            '5',
            'Ativo',
            'Produto importado.',
        ]

    def test_valida_produto_novo(self):
        resultado = validar_planilha_produtos(
            arquivo=criar_planilha([
                self.linha_valida()
            ]),
            matriz=self.matriz,
        )

        self.assertTrue(
            resultado['valido']
        )
        self.assertEqual(
            resultado['resumo']['validos'],
            1
        )
        self.assertEqual(
            resultado['resumo']['novos'],
            1
        )
        self.assertEqual(
            resultado['linhas'][0]['acao_prevista'],
            'novo'
        )

    def test_identifica_produto_existente(self):
        Produto.objects.create(
            matriz=self.matriz,
            categoria=self.categoria,
            marca=self.marca,
            unidade_medida=self.unidade,
            codigo_interno='PROD-001',
            nome='Produto Existente',
            custo_base='40.00',
            preco_venda='80.00',
        )

        resultado = validar_planilha_produtos(
            arquivo=criar_planilha([
                self.linha_valida()
            ]),
            matriz=self.matriz,
        )

        self.assertEqual(
            resultado['resumo']['atualizar'],
            1
        )
        self.assertEqual(
            resultado['linhas'][0]['acao_prevista'],
            'atualizar'
        )
        self.assertTrue(
            resultado['linhas'][0]['produto_id']
        )

    def test_detecta_unidade_inexistente(self):
        linha = self.linha_valida()
        linha[7] = 'CX'

        resultado = validar_planilha_produtos(
            arquivo=criar_planilha([
                linha
            ]),
            matriz=self.matriz,
        )

        self.assertEqual(
            resultado['resumo']['invalidos'],
            1
        )
        self.assertIn(
            'Unidade não encontrada',
            resultado['linhas'][0]['erros'][0]
        )

    def test_detecta_codigo_duplicado_na_planilha(self):
        resultado = validar_planilha_produtos(
            arquivo=criar_planilha([
                self.linha_valida(),
                self.linha_valida(
                    nome='Outro Produto',
                    sku='SKU-002',
                    gtin='7891234567891',
                ),
            ]),
            matriz=self.matriz,
        )

        self.assertEqual(
            resultado['resumo']['invalidos'],
            1
        )
        self.assertIn(
            'Código interno duplicado',
            ' '.join(
                resultado['linhas'][1]['erros']
            )
        )

    def test_detecta_gtin_invalido(self):
        resultado = validar_planilha_produtos(
            arquivo=criar_planilha([
                self.linha_valida(
                    gtin='123'
                )
            ]),
            matriz=self.matriz,
        )

        self.assertEqual(
            resultado['resumo']['invalidos'],
            1
        )
        self.assertIn(
            'GTIN',
            ' '.join(
                resultado['linhas'][0]['erros']
            )
        )

    def test_detecta_colunas_ausentes(self):
        resultado = validar_planilha_produtos(
            arquivo=criar_planilha(
                [
                    [
                        'PROD-001',
                        'Produto',
                    ]
                ],
                colunas=[
                    'Código Interno',
                    'Nome',
                ],
            ),
            matriz=self.matriz,
        )

        self.assertFalse(
            resultado['valido']
        )
        self.assertIn(
            'Unidade',
            resultado['erro_estrutura']
        )

    def test_gera_modelo_excel(self):
        arquivo = gerar_modelo_importacao_produtos()

        workbook = load_workbook(
            arquivo
        )

        worksheet = workbook['Produtos']

        self.assertEqual(
            worksheet['A1'].value,
            'Código Interno'
        )
        self.assertEqual(
            worksheet['B2'].value,
            'Produto de exemplo'
        )

    def test_template_confirmacao_carrega(self):
        template = get_template(
            'produtos/importacao/confirmar.html'
        )

        self.assertIsNotNone(
            template
        )
