SESSAO_NOVA_EMPRESA = 'wizard_nova_empresa'
SESSAO_NOVA_EMPRESA_SENHA = 'wizard_nova_empresa_senha'


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


def salvar_senha_admin_wizard(request, senha):
    request.session[SESSAO_NOVA_EMPRESA_SENHA] = senha
    request.session.modified = True


def get_senha_admin_wizard(request):
    return request.session.get(SESSAO_NOVA_EMPRESA_SENHA)


def limpar_wizard_nova_empresa(request):
    if SESSAO_NOVA_EMPRESA in request.session:
        del request.session[SESSAO_NOVA_EMPRESA]

    if SESSAO_NOVA_EMPRESA_SENHA in request.session:
        del request.session[SESSAO_NOVA_EMPRESA_SENHA]

    request.session.modified = True


def wizard_nova_empresa_completo(dados_wizard):
    return (
        'matriz' in dados_wizard
        and 'loja' in dados_wizard
        and 'admin' in dados_wizard
    )