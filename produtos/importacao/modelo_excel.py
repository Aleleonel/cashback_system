from core.importacao import (
    criar_resposta_download_excel,
    gerar_modelo_excel,
)


COLUNAS_MODELO_PRODUTOS = [
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


LINHAS_EXEMPLO_PRODUTOS = [
    [
        'PROD-001',
        'Produto de exemplo',
        'SKU-001',
        '7891234567890',
        '21069030',
        'Suplementos',
        'Marca Exemplo',
        'UN',
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
        'Descrição opcional do produto.',
    ]
]


def gerar_modelo_importacao_produtos():
    return gerar_modelo_excel(
        nome_aba='Produtos',
        colunas=COLUNAS_MODELO_PRODUTOS,
        linhas_exemplo=LINHAS_EXEMPLO_PRODUTOS,
    )


def criar_download_modelo_produtos():
    arquivo = gerar_modelo_importacao_produtos()

    return criar_resposta_download_excel(
        arquivo=arquivo,
        nome_arquivo=(
            'modelo_importacao_produtos.xlsx'
        ),
    )
