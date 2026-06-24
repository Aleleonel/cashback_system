import unicodedata


def limpar_numero(valor):
    return ''.join(filter(str.isdigit, valor or ''))


def normalizar_texto(valor):
    if not valor:
        return ''

    valor = str(valor).strip().lower()

    valor = unicodedata.normalize('NFKD', valor)

    valor = ''.join(
        caractere for caractere in valor
        if not unicodedata.combining(caractere)
    )

    return valor