from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from fiscal.constants import (
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import NCMForm
from fiscal.selectors import get_ncm, get_ncms
from fiscal.services import criar_ncm, editar_ncm


def _aplicar_erros(form, erro):
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


def _obter_ncm_ou_404(ncm_id):
    try:
        return get_ncm(ncm_id=ncm_id)
    except ObjectDoesNotExist as erro:
        raise Http404("NCM nao encontrado.") from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_ncms(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"

    pagina = Paginator(
        get_ncms(
            busca=busca,
            somente_ativos=somente_ativos,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/ncm/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "somente_ativos": somente_ativos,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_ncm_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = NCMForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_ncm(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "NCM criado com sucesso.")
            return redirect("fiscal:lista_ncms")

    return render(
        request,
        "fiscal/ncm/form.html",
        {
            "form": form,
            "titulo": "Novo NCM",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_ncm_view(request, ncm_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    ncm = _obter_ncm_ou_404(ncm_id)
    form = NCMForm(request.POST or None, instance=ncm)

    if request.method == "POST" and form.is_valid():
        try:
            editar_ncm(
                ncm=ncm,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "NCM atualizado com sucesso.")
            return redirect("fiscal:lista_ncms")

    return render(
        request,
        "fiscal/ncm/form.html",
        {
            "form": form,
            "titulo": "Editar NCM",
            "ncm": ncm,
        },
    )
