from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_EMPRESA_USUARIOS_GERENCIAR

from .catalogo import listar_grupos_configuracao
from .forms import ConfiguracaoComercialForm
from .services import (
    atualizar_configuracao_comercial,
    obter_ou_criar_configuracao_comercial,
)
from .decorators import (
    central_configuracoes_required,
    configuracoes_criticas_required,
)


@central_configuracoes_required
def inicio(request):
    contexto_acesso = request.contexto_configuracoes
    grupos = listar_grupos_configuracao(
        incluir_criticos=contexto_acesso["pode_configuracoes_criticas"]
    )

    return render(
        request,
        "configuracoes/inicio.html",
        {
            "grupos": grupos,
            "contexto_configuracoes": contexto_acesso,
        },
    )


@configuracoes_criticas_required
def criticas(request):
    return render(
        request,
        "configuracoes/criticas.html",
        {
            "contexto_configuracoes": request.contexto_configuracoes,
        },
    )

@central_configuracoes_required
def empresa(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/empresa.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_empresa": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

@central_configuracoes_required
@require_permission(PERMISSAO_EMPRESA_USUARIOS_GERENCIAR)
def usuarios_permissoes(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/usuarios_permissoes.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_usuarios": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

@central_configuracoes_required
def clientes_cashback(request):
    contexto_acesso = request.contexto_configuracoes

    return render(
        request,
        "configuracoes/clientes_cashback.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "pode_operar_clientes_cashback": (
                contexto_acesso["escopo"] == "empresa"
                and contexto_acesso["matriz"] is not None
            ),
        },
    )

@central_configuracoes_required
def vendas_comissoes(request):
    contexto_acesso = request.contexto_configuracoes

    secoes = [
        {
            "titulo": "Regras Comerciais",
            "descricao": "Parâmetros gerais que orientam vendas, descontos e condições comerciais.",
            "icone": "bi-sliders",
            "url_name": "configuracoes:regras_comerciais",
            "disponivel": True,
        },
        {
            "titulo": "Tabelas de Preços",
            "descricao": "Organização das tabelas e políticas de preços utilizadas pelo sistema.",
            "icone": "bi-tags",
        },
        {
            "titulo": "Promoções",
            "descricao": "Central futura para campanhas promocionais e condições especiais.",
            "icone": "bi-megaphone",
        },
        {
            "titulo": "Atacado",
            "descricao": "Parâmetros futuros para vendas em quantidade e condições de atacado.",
            "icone": "bi-box-seam",
        },
        {
            "titulo": "Cashback Comercial",
            "descricao": "Integração futura das regras comerciais com benefícios de cashback.",
            "icone": "bi-arrow-repeat",
        },
        {
            "titulo": "Voucher",
            "descricao": "Configurações futuras de vouchers, validade e regras de utilização.",
            "icone": "bi-ticket-perforated",
        },
        {
            "titulo": "Brindes",
            "descricao": "Critérios futuros para concessão e controle de brindes nas vendas.",
            "icone": "bi-gift",
        },
        {
            "titulo": "Comissões",
            "descricao": "Estrutura futura para regras, percentuais e cálculo de comissões.",
            "icone": "bi-percent",
        },
    ]

    return render(
        request,
        "configuracoes/vendas_comissoes.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "secoes": secoes,
        },
    )

@central_configuracoes_required
def regras_comerciais(request):
    contexto_acesso = request.contexto_configuracoes
    matriz = contexto_acesso["matriz"]
    pode_editar = (
        contexto_acesso["escopo"] == "empresa"
        and matriz is not None
    )

    configuracao = None
    if matriz is not None:
        configuracao = obter_ou_criar_configuracao_comercial(matriz=matriz)

    if request.method == "POST":
        if not pode_editar or configuracao is None:
            messages.error(
                request,
                "Selecione um contexto de empresa válido para alterar as regras comerciais.",
            )
            return redirect("configuracoes:regras_comerciais")

        form = ConfiguracaoComercialForm(
            request.POST,
            instance=configuracao,
            pode_editar=True,
        )
        if form.is_valid():
            atualizar_configuracao_comercial(
                configuracao=configuracao,
                dados=form.cleaned_data,
            )
            messages.success(request, "Regras comerciais atualizadas com sucesso.")
            return redirect("configuracoes:regras_comerciais")
    else:
        form = ConfiguracaoComercialForm(
            instance=configuracao,
            pode_editar=pode_editar,
        )

    return render(
        request,
        "configuracoes/regras_comerciais.html",
        {
            "contexto_configuracoes": contexto_acesso,
            "configuracao": configuracao,
            "form": form,
            "pode_editar_regras": pode_editar,
        },
    )

