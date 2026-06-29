SESSAO_NOVA_EMPRESA = 'wizard_nova_empresa'


def get_dados_wizard_nova_empresa(request):

    return request.session.get(
        SESSAO_NOVA_EMPRESA,
        {}
    )


def salvar_dados_wizard_nova_empresa(request, chave, dados):

    dados_wizard = get_dados_wizard_nova_empresa(request)

    dados_wizard[chave] = dados

    request.session[SESSAO_NOVA_EMPRESA] = dados_wizard

    request.session.modified = True


def limpar_wizard_nova_empresa(request):

    if SESSAO_NOVA_EMPRESA in request.session:
        del request.session[SESSAO_NOVA_EMPRESA]

        request.session.modified = True


def wizard_nova_empresa_completo(dados_wizard):

    return (
        'matriz' in dados_wizard
        and 'loja' in dados_wizard
        and 'admin' in dados_wizard
    )