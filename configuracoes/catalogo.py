from dataclasses import dataclass


@dataclass(frozen=True)
class GrupoConfiguracao:
    codigo: str
    titulo: str
    descricao: str
    icone: str
    url_name: str | None = None
    disponivel: bool = False
    critico: bool = False


GRUPOS_CONFIGURACAO = (
    GrupoConfiguracao(
codigo="empresa",
        titulo="Empresa e lojas",
        descricao="Dados empresariais, unidades e parâmetros da matriz.",
        icone="bi-buildings",
        url_name="configuracoes:empresa",
        disponivel=True,
    ),
    GrupoConfiguracao(
codigo="usuarios",
        titulo="Usuários e permissões",
        descricao="Acessos, perfis e permissões administrativas.",
        icone="bi-people",
        url_name="configuracoes:usuarios_permissoes",
        disponivel=True,
    ),
    GrupoConfiguracao(
        codigo="clientes_cashback",
        titulo="Clientes e cashback",
        descricao="Regras de identificação, benefícios e cashback.",
        icone="bi-person-heart",
    ),
    GrupoConfiguracao(
        codigo="produtos_estoque",
        titulo="Produtos e estoque",
        descricao="Parâmetros comerciais, inventário e disponibilidade.",
        icone="bi-boxes",
    ),
    GrupoConfiguracao(
        codigo="compras",
        titulo="Compras",
        descricao="Fornecedores, recebimentos e políticas de compra.",
        icone="bi-bag-check",
    ),
    GrupoConfiguracao(
        codigo="vendas_comissoes",
        titulo="Vendas e comissões",
        descricao="Regras de venda, vendedores e cálculo de comissões.",
        icone="bi-receipt",
    ),
    GrupoConfiguracao(
        codigo="caixa_pagamentos",
        titulo="Caixa e pagamentos",
        descricao="Abertura, fechamento e formas de pagamento.",
        icone="bi-cash-stack",
    ),
    GrupoConfiguracao(
        codigo="financeiro_fiscal",
        titulo="Financeiro e fiscal",
        descricao="Contas a receber, parcelamento e emissão fiscal.",
        icone="bi-calculator",
    ),
    GrupoConfiguracao(
        codigo="notificacoes",
        titulo="Notificações",
        descricao="E-mail, mensagens e comunicações automáticas.",
        icone="bi-bell",
    ),
    GrupoConfiguracao(
        codigo="seguranca",
        titulo="Segurança e integrações",
        descricao="Parâmetros críticos e integrações da plataforma.",
        icone="bi-shield-lock",
        url_name="configuracoes:criticas",
        disponivel=True,
        critico=True,
    ),
    GrupoConfiguracao(
        codigo="auditoria",
        titulo="Auditoria",
        descricao="Rastreamento e histórico de alterações.",
        icone="bi-clock-history",
    ),
)


def listar_grupos_configuracao(*, incluir_criticos):
    return tuple(
        grupo
        for grupo in GRUPOS_CONFIGURACAO
        if incluir_criticos or not grupo.critico
    )
