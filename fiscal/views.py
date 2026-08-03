from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from core.services import get_contexto_operacional_usuario
from fiscal.constants import (
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import OrigemMercadoriaForm
from fiscal.selectors import (
    get_origem_mercadoria,
    get_origens_mercadoria,
)
from fiscal.services import (
    criar_origem_mercadoria,
    editar_origem_mercadoria,
)


def _aplicar_erros_no_form(*, form, erro):
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(
                    campo if campo in form.fields else None,
                    mensagem,
                )
        return

    for mensagem in erro.messages:
        form.add_error(None, mensagem)


def _obter_origem_ou_404(*, origem_id):
    try:
        return get_origem_mercadoria(
            origem_id=origem_id,
        )
    except ObjectDoesNotExist as erro:
        raise Http404(
            "Origem da mercadoria nao encontrada."
        ) from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def inicio(request):
    contexto = get_contexto_operacional_usuario(request.user)

    modulos = (
        {
            "titulo": "Origens da mercadoria",
            "descricao": (
                "Codigos oficiais usados na classificacao fiscal "
                "dos produtos."
            ),
            "icone": "bi-globe-americas",
            "url_name": "fiscal:lista_origens_mercadoria",
            "disponivel": True,
        },
        {
            "titulo": "CST ICMS",
            "descricao": "Situacoes tributarias do ICMS usadas na classificacao fiscal.",
            "icone": "bi-percent",
            "url_name": "fiscal:lista_csts_icms",
            "disponivel": True,
        },
        {
            "titulo": "CSOSN",
            "descricao": "Situacoes tributarias do Simples Nacional para classificacao fiscal.",
            "icone": "bi-diagram-3",
            "url_name": "fiscal:lista_csosns",
            "disponivel": True,
        },
        {
            "titulo": "CFOP",
            "descricao": "Codigos fiscais de operacoes e prestacoes para compras, vendas e devolucoes.",
            "icone": "bi-arrow-left-right",
            "url_name": "fiscal:lista_cfops",
            "disponivel": True,
        },
        {
            "titulo": "NCM",
            "descricao": "Catalogo de classificacoes fiscais para futura vinculacao aos produtos.",
            "icone": "bi-list-ol",
            "url_name": "fiscal:lista_ncms",
            "disponivel": True,
        },
        {
            "titulo": "CST PIS",
            "descricao": "Situacoes tributarias do PIS para entradas e saidas.",
            "icone": "bi-percent",
            "url_name": "fiscal:lista_csts_pis",
            "disponivel": True,
        },
        {
            "titulo": "CST COFINS",
            "descricao": "Situacoes tributarias do COFINS para entradas e saidas.",
            "icone": "bi-percent",
            "url_name": "fiscal:lista_csts_cofins",
            "disponivel": True,
        },
        {
            "titulo": "CST IPI",
            "descricao": "Situacoes tributarias do IPI para entradas e saidas.",
            "icone": "bi-percent",
            "url_name": "fiscal:lista_csts_ipi",
            "disponivel": True,
        },
        {
            "titulo": "CEST",
            "descricao": "Catalogo de produtos sujeitos a substituicao tributaria.",
            "icone": "bi-tags",
            "url_name": "fiscal:lista_cests",
            "disponivel": True,
        },
        {
            "titulo": "Beneficios fiscais",
            "descricao": "Catalogo de beneficios, desoneracoes, reducoes e creditos fiscais.",
            "icone": "bi-award",
            "url_name": "fiscal:lista_beneficios_fiscais",
            "disponivel": True,
        },
        {
            "titulo": "Regras fiscais",
            "descricao": "Condicoes, resultados e parametros para selecao tributaria.",
            "icone": "bi-diagram-3",
            "url_name": "fiscal:lista_regras_fiscais",
            "disponivel": True,
        },
        {
            "titulo": "Demais cadastros tributarios",
            "descricao": "CFOP, CST, CSOSN, CEST e regras fiscais.",
            "icone": "bi-journal-text",
            "url_name": "",
            "disponivel": False,
        },
        {
            "titulo": "Produtos fiscais",
            "descricao": "Parametros tributarios vinculados aos produtos.",
            "icone": "bi-box-seam",
            "url_name": "",
            "disponivel": False,
        },
        {
            "titulo": "Emissao fiscal",
            "descricao": "Preparacao para NFC-e, contingencia e DANFE.",
            "icone": "bi-receipt",
            "url_name": "",
            "disponivel": False,
        },
    )

    return render(
        request,
        "fiscal/inicio.html",
        {
            "matriz": contexto["matriz"],
            "loja": contexto.get("loja"),
            "modulos": modulos,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_origens_mercadoria(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativas = request.GET.get("ativas") == "1"

    origens = get_origens_mercadoria(
        busca=busca,
        somente_ativas=somente_ativas,
    )

    pagina = Paginator(origens, 25).get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "fiscal/origens_mercadoria/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "somente_ativas": somente_ativas,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_origem_mercadoria_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)

    if request.method == "POST":
        form = OrigemMercadoriaForm(request.POST)

        if form.is_valid():
            try:
                criar_origem_mercadoria(
                    dados=form.cleaned_data,
                    usuario_executor=request.user,
                    matriz=matriz,
                    loja=loja,
                    request=request,
                )
            except ValidationError as erro:
                _aplicar_erros_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(
                    request,
                    "Origem da mercadoria criada com sucesso.",
                )
                return redirect(
                    "fiscal:lista_origens_mercadoria"
                )
    else:
        form = OrigemMercadoriaForm()

    return render(
        request,
        "fiscal/origens_mercadoria/form.html",
        {
            "form": form,
            "titulo": "Nova origem da mercadoria",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_origem_mercadoria_view(request, origem_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    origem = _obter_origem_ou_404(
        origem_id=origem_id,
    )

    if request.method == "POST":
        form = OrigemMercadoriaForm(
            request.POST,
            instance=origem,
        )

        if form.is_valid():
            try:
                editar_origem_mercadoria(
                    origem=origem,
                    dados=form.cleaned_data,
                    usuario_executor=request.user,
                    matriz=matriz,
                    loja=loja,
                    request=request,
                )
            except ValidationError as erro:
                _aplicar_erros_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(
                    request,
                    "Origem da mercadoria atualizada com sucesso.",
                )
                return redirect(
                    "fiscal:lista_origens_mercadoria"
                )
    else:
        form = OrigemMercadoriaForm(
            instance=origem,
        )

    return render(
        request,
        "fiscal/origens_mercadoria/form.html",
        {
            "form": form,
            "titulo": "Editar origem da mercadoria",
            "origem": origem,
        },
    )
