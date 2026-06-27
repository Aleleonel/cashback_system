from django.core.exceptions import PermissionDenied

PERMISSAO_PLATAFORMA_PAINEL_MASTER = 'plataforma.painel_master'
PERMISSAO_DASHBOARD = 'dashboard.visualizar'
PERMISSAO_CLIENTES_VISUALIZAR = 'clientes.visualizar'
PERMISSAO_CLIENTES_CRIAR = 'clientes.criar'
PERMISSAO_CLIENTES_EDITAR = 'clientes.editar'
PERMISSAO_CLIENTES_IMPORTAR = 'clientes.importar'

PERMISSAO_CASHBACK_NOVA_COMPRA = 'cashback.nova_compra'
PERMISSAO_CASHBACK_EXTRATO = 'cashback.extrato'

PERMISSAO_CAMPANHAS_VISUALIZAR = 'campanhas.visualizar'
PERMISSAO_CAMPANHAS_DISPARAR = 'campanhas.disparar'
PERMISSAO_CAMPANHAS_CONFIGURAR = 'campanhas.configurar'
PERMISSAO_CAMPANHAS_TEMPLATES = 'campanhas.templates'


PERMISSOES_POR_PERFIL = {
    'master': {
        PERMISSAO_DASHBOARD,
        PERMISSAO_CLIENTES_VISUALIZAR,
        PERMISSAO_CLIENTES_CRIAR,
        PERMISSAO_CLIENTES_EDITAR,
        PERMISSAO_CLIENTES_IMPORTAR,
        PERMISSAO_CASHBACK_NOVA_COMPRA,
        PERMISSAO_CASHBACK_EXTRATO,
        PERMISSAO_CAMPANHAS_VISUALIZAR,
        PERMISSAO_CAMPANHAS_DISPARAR,
        PERMISSAO_CAMPANHAS_CONFIGURAR,
        PERMISSAO_CAMPANHAS_TEMPLATES,
        
    },
    'admin_loja': {
        PERMISSAO_DASHBOARD,
        PERMISSAO_CLIENTES_VISUALIZAR,
        PERMISSAO_CLIENTES_CRIAR,
        PERMISSAO_CLIENTES_EDITAR,
        PERMISSAO_CLIENTES_IMPORTAR,
        PERMISSAO_CASHBACK_NOVA_COMPRA,
        PERMISSAO_CASHBACK_EXTRATO,
        PERMISSAO_CAMPANHAS_VISUALIZAR,
        PERMISSAO_CAMPANHAS_DISPARAR,
        PERMISSAO_CAMPANHAS_TEMPLATES,
    },
    'operador': {
        PERMISSAO_DASHBOARD,
        PERMISSAO_CLIENTES_VISUALIZAR,
        PERMISSAO_CLIENTES_CRIAR,
        PERMISSAO_CASHBACK_NOVA_COMPRA,
        PERMISSAO_CASHBACK_EXTRATO,
    },
}


def usuario_tem_permissao(usuario, permissao):
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if permissao == PERMISSAO_PLATAFORMA_PAINEL_MASTER:
        return False

    if not getattr(usuario, 'ativo', False):
        return False

    permissoes = PERMISSOES_POR_PERFIL.get(
        usuario.perfil,
        set()
    )

    return permissao in permissoes


def exigir_permissao(usuario, permissao):
    if not usuario_tem_permissao(usuario, permissao):
        raise PermissionDenied(
            'Você não tem permissão para acessar este recurso.'
        )