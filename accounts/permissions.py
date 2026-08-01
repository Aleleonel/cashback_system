# PDV-ACL-01 - IMPORTS CENTRALIZADOS
from pdv.constants import (
    PERMISSAO_PDV_ABRIR_CAIXA,
    PERMISSAO_PDV_AUTORIZAR_BRINDE,
    PERMISSAO_PDV_AUTORIZAR_DESCONTO,
    PERMISSAO_PDV_CANCELAR_VENDA,
    PERMISSAO_PDV_FECHAR_CAIXA,
    PERMISSAO_PDV_OPERAR,
    PERMISSAO_PDV_SANGRIA,
    PERMISSAO_PDV_SUPRIMENTO,
    PERMISSAO_PDV_VISUALIZAR,
)

# ==========================================================
# PLATAFORMA
# ==========================================================

PERMISSAO_PLATAFORMA_PAINEL_MASTER = 'plataforma.painel_master'


# ==========================================================
# MINHA EMPRESA
# ==========================================================

PERMISSAO_EMPRESA_LOJAS_GERENCIAR = 'empresa.lojas_gerenciar'
PERMISSAO_EMPRESA_CONFIGURAR_CASHBACK = 'empresa.configurar_cashback'
PERMISSAO_VOUCHERS_GERENCIAR = 'vouchers.gerenciar'


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
# PRODUTOS
# ==========================================================

PERMISSAO_PRODUTOS_VISUALIZAR = 'produtos.visualizar'
PERMISSAO_PRODUTOS_CRIAR = 'produtos.criar'
PERMISSAO_PRODUTOS_EDITAR = 'produtos.editar'
PERMISSAO_PRODUTOS_IMPORTAR = 'produtos.importar'
PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES = (
    'produtos.gerenciar_auxiliares'
)


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
PERMISSAO_EMPRESA_USUARIOS_GERENCIAR = (
    'empresa.usuarios_gerenciar'
)


# ==========================================================
# GRUPOS DE PERMISSOES
# ==========================================================

PERMISSOES_EMPRESA = {
    PERMISSAO_EMPRESA_LOJAS_GERENCIAR,
    PERMISSAO_EMPRESA_CONFIGURAR_CASHBACK,
    PERMISSAO_EMPRESA_USUARIOS_GERENCIAR,
}

PERMISSOES_CLIENTES = {
    PERMISSAO_CLIENTES_VISUALIZAR,
    PERMISSAO_CLIENTES_CRIAR,
    PERMISSAO_CLIENTES_EDITAR,
    PERMISSAO_CLIENTES_IMPORTAR,
}

PERMISSOES_PRODUTOS = {
    PERMISSAO_PRODUTOS_VISUALIZAR,
    PERMISSAO_PRODUTOS_CRIAR,
    PERMISSAO_PRODUTOS_EDITAR,
    PERMISSAO_PRODUTOS_IMPORTAR,
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
}

PERMISSOES_CASHBACK = {
    PERMISSAO_CASHBACK_NOVA_COMPRA,
    PERMISSAO_CASHBACK_EXTRATO,
}

PERMISSOES_VOUCHERS = {
    PERMISSAO_VOUCHERS_GERENCIAR,
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


# PDV-ACL-01 - GRUPOS DE PERMISSOES
PERMISSOES_PDV_OPERADOR = {
    PERMISSAO_PDV_VISUALIZAR,
    PERMISSAO_PDV_OPERAR,
    PERMISSAO_PDV_ABRIR_CAIXA,
}

PERMISSOES_PDV_SUPERVISAO = {
    PERMISSAO_PDV_FECHAR_CAIXA,
    PERMISSAO_PDV_CANCELAR_VENDA,
    PERMISSAO_PDV_AUTORIZAR_DESCONTO,
    PERMISSAO_PDV_AUTORIZAR_BRINDE,
    PERMISSAO_PDV_SUPRIMENTO,
    PERMISSAO_PDV_SANGRIA,
}

PERMISSOES_PDV = PERMISSOES_PDV_OPERADOR | PERMISSOES_PDV_SUPERVISAO


# ==========================================================
# PERFIS
# ==========================================================

# PDV-ACL-01 - PERFIS CONSOLIDADOS
PERMISSOES_POR_PERFIL = {
    'master': (
        PERMISSOES_CLIENTES
        | PERMISSOES_CASHBACK
        | PERMISSOES_CAMPANHAS
        | PERMISSOES_RELATORIOS
        | PERMISSOES_EMPRESA
        | PERMISSOES_VOUCHERS
        | PERMISSOES_PRODUTOS
        | PERMISSOES_PDV
    ),
    'admin_loja': (
        PERMISSOES_CLIENTES
        | PERMISSOES_EMPRESA
        | PERMISSOES_CASHBACK
        | PERMISSOES_VOUCHERS
        | PERMISSOES_PRODUTOS
        | {
            PERMISSAO_CAMPANHAS_VISUALIZAR,
            PERMISSAO_CAMPANHAS_DISPARAR,
            PERMISSAO_CAMPANHAS_CONFIGURAR,
            PERMISSAO_CAMPANHAS_TEMPLATES,
        }
        | PERMISSOES_RELATORIOS
        | PERMISSOES_PDV
    ),
    'operador': {
        PERMISSAO_DASHBOARD,
        PERMISSAO_RELATORIOS_DASHBOARD,
        PERMISSAO_CLIENTES_VISUALIZAR,
        PERMISSAO_CLIENTES_CRIAR,
        PERMISSAO_PRODUTOS_VISUALIZAR,
        PERMISSAO_PRODUTOS_CRIAR,
        PERMISSAO_CASHBACK_NOVA_COMPRA,
        PERMISSAO_CASHBACK_EXTRATO,
    } | PERMISSOES_PDV_OPERADOR,
}


def get_permissoes_extras_disponiveis():
    return [
        {
            'codigo': PERMISSAO_PRODUTOS_EDITAR,
            'nome': 'Produtos: editar',
            'grupo': 'Produtos',
        },
        {
            'codigo': PERMISSAO_PRODUTOS_IMPORTAR,
            'nome': 'Produtos: importar planilhas',
            'grupo': 'Produtos',
        },
        {
            'codigo': PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
            'nome': (
                'Produtos: gerenciar categorias, marcas e unidades'
            ),
            'grupo': 'Produtos',
        },
        {
            'codigo': PERMISSAO_CAMPANHAS_VISUALIZAR,
            'nome': 'Campanhas: visualizar',
            'grupo': 'Campanhas',
        },
        {
            'codigo': PERMISSAO_CAMPANHAS_DISPARAR,
            'nome': 'Campanhas: disparar',
            'grupo': 'Campanhas',
        },
        {
            'codigo': PERMISSAO_CAMPANHAS_TEMPLATES,
            'nome': 'Campanhas: templates',
            'grupo': 'Campanhas',
        },
        {
            'codigo': PERMISSAO_CAMPANHAS_CONFIGURAR,
            'nome': 'Campanhas: configurar',
            'grupo': 'Campanhas',
        },
        {
            'codigo': PERMISSAO_CLIENTES_IMPORTAR,
            'nome': 'Clientes: importar',
            'grupo': 'Clientes',
        },
    ]

# CFG-PDV-01 - PERMISSOES PDV NOS CHECKBOXES
_get_permissoes_extras_disponiveis_sem_pdv = get_permissoes_extras_disponiveis


def get_permissoes_extras_disponiveis():
    from pdv.constants import (
        PERMISSAO_PDV_ABRIR_CAIXA,
        PERMISSAO_PDV_AUTORIZAR_BRINDE,
        PERMISSAO_PDV_AUTORIZAR_DESCONTO,
        PERMISSAO_PDV_CANCELAR_VENDA,
        PERMISSAO_PDV_FECHAR_CAIXA,
        PERMISSAO_PDV_OPERAR,
        PERMISSAO_PDV_SANGRIA,
        PERMISSAO_PDV_SUPRIMENTO,
        PERMISSAO_PDV_VISUALIZAR,
    )

    itens = list(_get_permissoes_extras_disponiveis_sem_pdv())
    codigos_existentes = {item["codigo"] for item in itens}

    permissoes_pdv = [
        {"codigo": PERMISSAO_PDV_VISUALIZAR, "nome": "Visualizar PDV", "grupo": "PDV / Frente de Caixa"},
        {"codigo": PERMISSAO_PDV_OPERAR, "nome": "Operar o PDV", "grupo": "PDV / Frente de Caixa"},
        {"codigo": PERMISSAO_PDV_ABRIR_CAIXA, "nome": "Abrir caixa", "grupo": "PDV / Caixa"},
        {"codigo": PERMISSAO_PDV_FECHAR_CAIXA, "nome": "Fechar caixa", "grupo": "PDV / Caixa"},
        {"codigo": PERMISSAO_PDV_SUPRIMENTO, "nome": "Registrar suprimento", "grupo": "PDV / Caixa"},
        {"codigo": PERMISSAO_PDV_SANGRIA, "nome": "Registrar sangria", "grupo": "PDV / Caixa"},
        {"codigo": PERMISSAO_PDV_CANCELAR_VENDA, "nome": "Cancelar venda", "grupo": "PDV / Operacoes"},
        {"codigo": PERMISSAO_PDV_AUTORIZAR_DESCONTO, "nome": "Autorizar desconto", "grupo": "PDV / Autorizacoes"},
        {"codigo": PERMISSAO_PDV_AUTORIZAR_BRINDE, "nome": "Autorizar brinde", "grupo": "PDV / Autorizacoes"},
    ]

    itens.extend(
        item
        for item in permissoes_pdv
        if item["codigo"] not in codigos_existentes
    )
    return itens
