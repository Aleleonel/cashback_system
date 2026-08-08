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


def get_configuracao_fiscal_matriz_para_edicao(*, matriz):
    """
    Retorna a configuracao existente da matriz, ativa ou inativa.

    Este selector e administrativo. O selector operacional
    get_configuracao_fiscal_matriz() continua retornando apenas configuracao
    ativa para preservar o contrato do Motor Fiscal.
    """
    if matriz is None:
        return None

    return (
        ConfiguracaoFiscalMatriz.objects
        .select_related("matriz")
        .filter(matriz=matriz)
        .first()
    )
