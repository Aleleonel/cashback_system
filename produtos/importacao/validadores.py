from decimal import Decimal

from core.importacao import (
    converter_booleano,
    converter_decimal,
    limpar_numero,
    limpar_texto,
    remover_acentos,
)


VALORES_BOOLEANOS_VALIDOS = {
    '1',
    '0',
    'sim',
    'nao',
    's',
    'n',
    'true',
    'false',
    'verdadeiro',
    'falso',
    'ativo',
    'inativo',
    'yes',
    'no',
}


def normalizar_chave(valor):
    return remover_acentos(
        limpar_texto(valor)
    ).strip().lower()


def normalizar_codigo(valor):
    return limpar_texto(
        valor
    ).upper()


def normalizar_identificador_numerico(valor):
    return limpar_numero(
        valor
    )


def interpretar_decimal(
    valor,
    *,
    campo,
    obrigatorio=False,
    padrao=None,
):
    texto = limpar_texto(
        valor
    )

    if not texto:
        if obrigatorio:
            if padrao is not None:
                return padrao, []

            return None, [
                f'{campo} é obrigatório.'
            ]

        return padrao, []

    convertido = converter_decimal(
        texto
    )

    if convertido is None:
        return None, [
            f'{campo} deve conter um valor numérico válido.'
        ]

    if convertido < 0:
        return None, [
            f'{campo} não pode ser negativo.'
        ]

    return convertido, []


def interpretar_inteiro(
    valor,
    *,
    campo,
):
    texto = limpar_texto(
        valor
    )

    if not texto:
        return None, []

    decimal, erros = interpretar_decimal(
        texto,
        campo=campo,
    )

    if erros:
        return None, erros

    if decimal != decimal.to_integral_value():
        return None, [
            f'{campo} deve conter um número inteiro.'
        ]

    return int(decimal), []


def interpretar_booleano(
    valor,
    *,
    campo,
    padrao=True,
):
    texto = normalizar_chave(
        valor
    )

    if not texto:
        return padrao, []

    if texto not in VALORES_BOOLEANOS_VALIDOS:
        return padrao, [
            (
                f'{campo} deve ser preenchido com '
                'Sim ou Não.'
            )
        ]

    return converter_booleano(
        texto,
        padrao=padrao,
    ), []


def serializar_decimal(valor):
    if valor is None:
        return ''

    if not isinstance(valor, Decimal):
        valor = Decimal(
            str(valor)
        )

    return format(
        valor,
        'f',
    )


def extrair_erros_validacao(erro):
    message_dict = getattr(
        erro,
        'message_dict',
        None,
    )

    if message_dict:
        mensagens = []

        for campo, erros in message_dict.items():
            for mensagem in erros:
                mensagens.append(
                    f'{campo}: {mensagem}'
                )

        return mensagens

    return list(
        getattr(
            erro,
            'messages',
            [str(erro)],
        )
    )
