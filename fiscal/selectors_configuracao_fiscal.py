from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz


def get_configuracao_fiscal_matriz(*, matriz):
    if matriz is None:
        return None

    return (
        ConfiguracaoFiscalMatriz.objects
        .select_related("matriz")
        .filter(matriz=matriz, ativa=True)
        .first()
    )
