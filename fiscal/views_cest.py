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
from fiscal.forms import CESTForm
from fiscal.selectors import get_cest, get_cests
from fiscal.services import criar_cest, editar_cest


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


def _obter_ou_404(cest_id):
    try:
        return get_cest(cest_id=cest_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CEST nao encontrado.") from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_cests(request):
    busca = request.GET.get("busca", "").strip()
    segmento = request.GET.get("segmento", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"

    pagina = Paginator(
        get_cests(
            busca=busca,
            segmento=segmento,
            somente_ativos=somente_ativos,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/cest/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "segmento": segmento,
            "somente_ativos": somente_ativos,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_cest_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CESTForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_cest(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(
                request,
                "CEST criado com sucesso.",
            )
            return redirect("fiscal:lista_cests")

    return render(
        request,
        "fiscal/cest/form.html",
        {"form": form, "titulo": "Novo CEST"},
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_cest_view(request, cest_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    cest = _obter_ou_404(cest_id)
    form = CESTForm(
        request.POST or None,
        instance=cest,
    )

    if request.method == "POST" and form.is_valid():
        try:
            editar_cest(
                cest=cest,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(
                request,
                "CEST atualizado com sucesso.",
            )
            return redirect("fiscal:lista_cests")

    return render(
        request,
        "fiscal/cest/form.html",
        {
            "form": form,
            "titulo": "Editar CEST",
            "cest": cest,
        },
    )
