from datetime import datetime

import pandas as pd

from django.db import transaction

from .models import Cliente


COLUNAS_OBRIGATORIAS = [
    'Nome',
    'CPF',
    'Nascimento',
    'Celular',
    'E-mail',
]


def normalizar_coluna(coluna):
    return (
        str(coluna)
        .strip()
        .lower()
        .replace(' ', '')
        .replace('-', '')
        .replace('_', '')
    )


def limpar_numero(valor):
    if pd.isna(valor):
        return ''

    return ''.join(filter(str.isdigit, str(valor)))


def limpar_texto(valor):
    if pd.isna(valor):
        return ''

    return str(valor).strip()


def converter_data(valor):
    if pd.isna(valor) or valor == '':
        return None

    if isinstance(valor, datetime):
        return valor.date()

    valor = str(valor).strip()

    formatos = [
        '%d/%m/%Y',
        '%Y-%m-%d',
    ]

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue

    return None


def converter_data_sessao(valor):
    if not valor:
        return None

    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        return None


def validar_planilha_clientes(*, arquivo, matriz):
    df = pd.read_excel(arquivo, dtype=str)

    mapa_colunas = {
        normalizar_coluna(coluna): coluna
        for coluna in df.columns
    }

    colunas_esperadas = {
        'nome': 'Nome',
        'cpf': 'CPF',
        'nascimento': 'Nascimento',
        'celular': 'Celular',
        'email': 'E-mail',
    }

    erros_estrutura = [
        nome_exibicao
        for chave, nome_exibicao in colunas_esperadas.items()
        if chave not in mapa_colunas
    ]

    if erros_estrutura:
        return {
            'valido': False,
            'erro_estrutura': (
                'Colunas obrigatórias ausentes: '
                + ', '.join(erros_estrutura)
            ),
            'linhas': [],
            'resumo': None,
        }

    cpfs_existentes = set(
        Cliente.objects.filter(
            matriz=matriz
        ).values_list(
            'cpf',
            flat=True
        )
    )

    linhas = []
    total_validos = 0
    total_invalidos = 0
    total_novos = 0
    total_atualizar = 0

    for indice, row in df.iterrows():
        numero_linha = indice + 2

        nome = limpar_texto(row.get(mapa_colunas['nome']))
        cpf = limpar_numero(row.get(mapa_colunas['cpf']))
        nascimento_original = row.get(mapa_colunas['nascimento'])
        nascimento = converter_data(nascimento_original)
        celular = limpar_numero(row.get(mapa_colunas['celular']))
        email = limpar_texto(row.get(mapa_colunas['email']))

        erros = []

        if not nome:
            erros.append('Nome obrigatório.')

        if nome and len(nome.split()) < 2:
            erros.append('Informe nome completo.')

        if not cpf:
            erros.append('CPF obrigatório.')

        if cpf and len(cpf) != 11:
            erros.append('CPF deve conter 11 números.')

        if nascimento_original and not pd.isna(nascimento_original) and nascimento is None:
            erros.append('Nascimento inválido.')

        if email and '@' not in email:
            erros.append('E-mail inválido.')

        status = 'novo'

        if cpf in cpfs_existentes:
            status = 'atualizar'

        valido = len(erros) == 0

        if valido:
            total_validos += 1

            if status == 'novo':
                total_novos += 1
            else:
                total_atualizar += 1
        else:
            total_invalidos += 1

        linhas.append({
            'linha': numero_linha,
            'nome': nome,
            'cpf': cpf,
            'nascimento': nascimento.isoformat() if nascimento else '',
            'celular': celular,
            'email': email,
            'status': status,
            'valido': valido,
            'erros': erros,
        })

    return {
        'valido': True,
        'erro_estrutura': None,
        'linhas': linhas,
        'resumo': {
            'total': len(linhas),
            'validos': total_validos,
            'invalidos': total_invalidos,
            'novos': total_novos,
            'atualizar': total_atualizar,
        },
    }


@transaction.atomic
def importar_clientes_validados(*, matriz, loja, linhas):
    linhas_validas = [
        linha for linha in linhas
        if linha['valido']
    ]

    cpfs = [
        linha['cpf']
        for linha in linhas_validas
    ]

    clientes_existentes = {
        cliente.cpf: cliente
        for cliente in Cliente.objects.filter(
            matriz=matriz,
            cpf__in=cpfs
        )
    }

    novos = []
    atualizar = []

    for linha in linhas_validas:
        nascimento = converter_data_sessao(
            linha.get('nascimento')
        )

        cliente = clientes_existentes.get(
            linha['cpf']
        )

        if cliente:
            cliente.nome = linha['nome']
            cliente.telefone = linha['celular']
            cliente.email = linha['email']
            cliente.data_nascimento = nascimento
            atualizar.append(cliente)

        else:
            novos.append(
                Cliente(
                    matriz=matriz,
                    loja_cadastro=loja,
                    nome=linha['nome'],
                    cpf=linha['cpf'],
                    telefone=linha['celular'],
                    email=linha['email'],
                    data_nascimento=nascimento,
                    aceita_email=True,
                    aceita_sms=False,
                    ativo=True,
                )
            )

    if novos:
        Cliente.objects.bulk_create(
            novos,
            batch_size=1000
        )

    if atualizar:
        Cliente.objects.bulk_update(
            atualizar,
            [
                'nome',
                'telefone',
                'email',
                'data_nascimento',
            ],
            batch_size=1000
        )

    return {
        'criados': len(novos),
        'atualizados': len(atualizar),
        'ignorados': 0,
    }