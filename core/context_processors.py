from accounts.permissions import (
    PERMISSAO_CASHBACK_NOVA_COMPRA,
    PERMISSAO_CAMPANHAS_CONFIGURAR,
    PERMISSAO_CAMPANHAS_DISPARAR,
    PERMISSAO_CAMPANHAS_TEMPLATES,
    PERMISSAO_CLIENTES_IMPORTAR,
    PERMISSAO_CLIENTES_VISUALIZAR,
    PERMISSAO_EMPRESA_CONFIGURAR_CASHBACK,
    PERMISSAO_EMPRESA_LOJAS_GERENCIAR,
    PERMISSAO_EMPRESA_USUARIOS_GERENCIAR,
    PERMISSAO_RELATORIOS_DASHBOARD,
)
from accounts.services import usuario_tem_permissao


def menu_permissoes(request):

    usuario = request.user

    if not usuario.is_authenticated:
        return {}

    return {
        'pode_ver_dashboard': usuario_tem_permissao(usuario, PERMISSAO_RELATORIOS_DASHBOARD),
        'pode_nova_compra': usuario_tem_permissao(usuario, PERMISSAO_CASHBACK_NOVA_COMPRA),
        'pode_ver_clientes': usuario_tem_permissao(usuario, PERMISSAO_CLIENTES_VISUALIZAR),
        'pode_importar_clientes': usuario_tem_permissao(usuario, PERMISSAO_CLIENTES_IMPORTAR),

        'pode_ver_campanhas': usuario_tem_permissao(usuario, PERMISSAO_CAMPANHAS_DISPARAR),
        'pode_configurar_campanhas': usuario_tem_permissao(usuario, PERMISSAO_CAMPANHAS_CONFIGURAR),
        'pode_templates_campanhas': usuario_tem_permissao(usuario, PERMISSAO_CAMPANHAS_TEMPLATES),

        'pode_empresa_lojas': usuario_tem_permissao(usuario, PERMISSAO_EMPRESA_LOJAS_GERENCIAR),
        'pode_empresa_usuarios': usuario_tem_permissao(usuario, PERMISSAO_EMPRESA_USUARIOS_GERENCIAR),
        'pode_empresa_cashback': usuario_tem_permissao(usuario, PERMISSAO_EMPRESA_CONFIGURAR_CASHBACK),
    }