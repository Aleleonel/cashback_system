from datetime import datetime

import pandas as pd

from django.db import transaction

from .models import Cliente
from .utils import limpar_numero, normalizar_texto

from .importacao import (
    validar_planilha_clientes_compartilhada,
)


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
    return validar_planilha_clientes_compartilhada(
        arquivo=arquivo,
        matriz=matriz,
    )

@transaction.atomic
def importar_clientes_validados(*, matriz, loja, linhas):
    linhas_validas = [
        linha for linha in linhas
        if linha['valido']
    ]

    cpfs_normalizados = [
        limpar_numero(linha['cpf'])
        for linha in linhas_validas
    ]

    clientes_existentes = {
        cliente.cpf_normalizado: cliente
        for cliente in Cliente.objects.filter(
            matriz=matriz,
            cpf_normalizado__in=cpfs_normalizados
        )
    }

    novos = []
    atualizar = []

    for linha in linhas_validas:
        nascimento = converter_data_sessao(
            linha.get('nascimento')
        )

        cpf_normalizado = limpar_numero(
            linha.get('cpf')
        )

        telefone_normalizado = limpar_numero(
            linha.get('celular')
        )

        nome_normalizado = normalizar_texto(
            linha.get('nome')
        )

        email_normalizado = normalizar_texto(
            linha.get('email')
        )

        cliente = clientes_existentes.get(
            cpf_normalizado
        )

        if cliente:
            cliente.nome = linha['nome']
            cliente.nome_normalizado = nome_normalizado
            cliente.telefone = linha['celular']
            cliente.telefone_normalizado = telefone_normalizado
            cliente.email = linha['email']
            cliente.email_normalizado = email_normalizado
            cliente.data_nascimento = nascimento
            cliente.cpf = linha['cpf']
            cliente.cpf_normalizado = cpf_normalizado

            atualizar.append(cliente)

        else:
            novos.append(
                Cliente(
                    matriz=matriz,
                    loja_cadastro=loja,
                    nome=linha['nome'],
                    nome_normalizado=nome_normalizado,
                    cpf=linha['cpf'],
                    cpf_normalizado=cpf_normalizado,
                    telefone=linha['celular'],
                    telefone_normalizado=telefone_normalizado,
                    email=linha['email'],
                    email_normalizado=email_normalizado,
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
                'nome_normalizado',
                'telefone',
                'telefone_normalizado',
                'email',
                'email_normalizado',
                'data_nascimento',
                'cpf',
                'cpf_normalizado',
            ],
            batch_size=1000
        )

    return {
        'criados': len(novos),
        'atualizados': len(atualizar),
        'ignorados': 0,
    }
