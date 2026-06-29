# ==========================================================
# PLATAFORMA
# ==========================================================

PERMISSAO_PLATAFORMA_PAINEL_MASTER = 'plataforma.painel_master'


# ==========================================================
# DASHBOARD / RELATORIOS
# ==========================================================

PERMISSAO_DASHBOARD = 'dashboard.visualizar'
PERMISSAO_RELATORIOS_DASHBOARD = 'relatorios.dashboard'


# ==========================================================
# CLIENTES
# ==========================================================

PERMISSAO_CLIENTES_VISUALIZAR = 'clientes.visualizar'
PERMISSAO_CLIENTES_CRIAR = 'clientes.criar'
PERMISSAO_CLIENTES_EDITAR = 'clientes.editar'
PERMISSAO_CLIENTES_IMPORTAR = 'clientes.importar'


# ==========================================================
# CASHBACK
# ==========================================================

PERMISSAO_CASHBACK_NOVA_COMPRA = 'cashback.nova_compra'
PERMISSAO_CASHBACK_EXTRATO = 'cashback.extrato'


# ==========================================================
# CAMPANHAS
# ==========================================================

PERMISSAO_CAMPANHAS_VISUALIZAR = 'campanhas.visualizar'
PERMISSAO_CAMPANHAS_DISPARAR = 'campanhas.disparar'
PERMISSAO_CAMPANHAS_CONFIGURAR = 'campanhas.configurar'
PERMISSAO_CAMPANHAS_TEMPLATES = 'campanhas.templates'


# ==========================================================
# GRUPOS DE PERMISSOES
# ==========================================================

PERMISSOES_CLIENTES = {
    PERMISSAO_CLIENTES_VISUALIZAR,
    PERMISSAO_CLIENTES_CRIAR,
    PERMISSAO_CLIENTES_EDITAR,
    PERMISSAO_CLIENTES_IMPORTAR,
}

PERMISSOES_CASHBACK = {
    PERMISSAO_CASHBACK_NOVA_COMPRA,
    PERMISSAO_CASHBACK_EXTRATO,
}

PERMISSOES_CAMPANHAS = {
    PERMISSAO_CAMPANHAS_VISUALIZAR,
    PERMISSAO_CAMPANHAS_DISPARAR,
    PERMISSAO_CAMPANHAS_CONFIGURAR,
    PERMISSAO_CAMPANHAS_TEMPLATES,
}

PERMISSOES_RELATORIOS = {
    PERMISSAO_DASHBOARD,
    PERMISSAO_RELATORIOS_DASHBOARD,
}


# ==========================================================
# PERFIS
# ==========================================================

PERMISSOES_POR_PERFIL = {
    'master': (
        PERMISSOES_CLIENTES
        | PERMISSOES_CASHBACK
        | PERMISSOES_CAMPANHAS
        | PERMISSOES_RELATORIOS
    ),

    'admin_loja': (
        PERMISSOES_CLIENTES
        | PERMISSOES_CASHBACK
        | {
            PERMISSAO_CAMPANHAS_VISUALIZAR,
            PERMISSAO_CAMPANHAS_DISPARAR,
            PERMISSAO_CAMPANHAS_CONFIGURAR,
            PERMISSAO_CAMPANHAS_TEMPLATES,
        }
        | PERMISSOES_RELATORIOS
    ),

    'operador': {
        PERMISSAO_DASHBOARD,
        PERMISSAO_RELATORIOS_DASHBOARD,
        PERMISSAO_CLIENTES_VISUALIZAR,
        PERMISSAO_CLIENTES_CRIAR,
        PERMISSAO_CASHBACK_NOVA_COMPRA,
        PERMISSAO_CASHBACK_EXTRATO,
    },
}