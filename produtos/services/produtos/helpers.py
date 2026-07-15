def somente_numeros(valor):
    return ''.join(
        caractere
        for caractere in str(valor or '')
        if caractere.isdigit()
    )


def normalizar_texto(valor):
    return str(valor or '').strip()


def normalizar_codigo(valor):
    return normalizar_texto(valor).upper()
