from core.importacao import (
    criar_resposta_download_excel,
    gerar_modelo_excel,
)


COLUNAS_MODELO_CLIENTES = [
    'Nome',
    'CPF',
    'Nascimento',
    'Celular',
    'E-mail',
]


LINHAS_EXEMPLO_CLIENTES = [
    [
        'João Silva',
        '12345678900',
        '01/01/1990',
        '11999999999',
        'joao@email.com',
    ]
]


def gerar_modelo_importacao_clientes():
    return gerar_modelo_excel(
        nome_aba='Clientes',
        colunas=COLUNAS_MODELO_CLIENTES,
        linhas_exemplo=LINHAS_EXEMPLO_CLIENTES,
    )


def criar_download_modelo_clientes():
    arquivo = gerar_modelo_importacao_clientes()

    return criar_resposta_download_excel(
        arquivo=arquivo,
        nome_arquivo=(
            'modelo_importacao_clientes.xlsx'
        ),
    )
