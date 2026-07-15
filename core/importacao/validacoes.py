from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata

import pandas as pd


FORMATOS_DATA_PADRAO = (
    '%d/%m/%Y',
    '%Y-%m-%d',
    '%d-%m-%Y',
)


def remover_acentos(valor):
    texto = str(valor or '')

    return ''.join(
        caractere
        for caractere in unicodedata.normalize(
            'NFKD',
            texto
        )
        if not unicodedata.combining(
            caractere
        )
    )


def normalizar_coluna(coluna):
    texto = remover_acentos(
        coluna
    ).strip().lower()

    return re.sub(
        r'[^a-z0-9]',
        '',
        texto
    )


def limpar_texto(valor):
    if valor is None or pd.isna(valor):
        return ''

    return str(valor).strip()


def limpar_numero(valor):
    return ''.join(
        caractere
        for caractere in limpar_texto(valor)
        if caractere.isdigit()
    )


def converter_data(
    valor,
    *,
    formatos=FORMATOS_DATA_PADRAO,
):
    if valor is None or pd.isna(valor):
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    texto = limpar_texto(valor)

    if not texto:
        return None

    for formato in formatos:
        try:
            return datetime.strptime(
                texto,
                formato
            ).date()
        except ValueError:
            continue

    return None


def serializar_data_sessao(valor):
    if valor is None:
        return ''

    if isinstance(valor, datetime):
        valor = valor.date()

    if isinstance(valor, date):
        return valor.isoformat()

    data_convertida = converter_data(
        valor
    )

    return (
        data_convertida.isoformat()
        if data_convertida
        else ''
    )


def converter_data_sessao(valor):
    if not valor:
        return None

    try:
        return datetime.strptime(
            str(valor),
            '%Y-%m-%d'
        ).date()
    except (TypeError, ValueError):
        return None


def converter_decimal(
    valor,
    *,
    padrao=None,
):
    if valor is None or pd.isna(valor):
        return padrao

    texto = limpar_texto(
        valor
    )

    if not texto:
        return padrao

    texto = texto.replace(
        'R$',
        ''
    ).strip()

    if ',' in texto and '.' in texto:
        texto = texto.replace(
            '.',
            ''
        ).replace(
            ',',
            '.'
        )
    elif ',' in texto:
        texto = texto.replace(
            ',',
            '.'
        )

    try:
        return Decimal(texto)
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return None


def converter_booleano(
    valor,
    *,
    padrao=False,
):
    if isinstance(valor, bool):
        return valor

    texto = remover_acentos(
        limpar_texto(valor)
    ).lower()

    if not texto:
        return padrao

    valores_verdadeiros = {
        '1',
        'sim',
        's',
        'true',
        'verdadeiro',
        'ativo',
        'yes',
    }

    valores_falsos = {
        '0',
        'nao',
        'n',
        'false',
        'falso',
        'inativo',
        'no',
    }

    if texto in valores_verdadeiros:
        return True

    if texto in valores_falsos:
        return False

    return padrao
