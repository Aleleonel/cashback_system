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
from fiscal.forms import CSTPISForm
from fiscal.models import CSTPIS
from fiscal.selectors import get_cst_pis, get_csts_pis
from fiscal.services import criar_cst_pis, editar_cst_pis


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


def _obter_ou_404(cst_pis_id):
    try:
        return get_cst_pis(cst_pis_id=cst_pis_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CST PIS nao encontrado.") from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_csts_pis(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"
    tipo_operacao = request.GET.get("tipo_operacao", "").strip()

    pagina = Paginator(
        get_csts_pis(
            busca=busca,
            somente_ativos=somente_ativos,
            tipo_operacao=tipo_operacao,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/cst_pis/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "somente_ativos": somente_ativos,
            "tipo_operacao": tipo_operacao,
            "tipos_operacao": CSTPIS.TIPO_OPERACAO_CHOICES,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_cst_pis_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CSTPISForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_cst_pis(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "CST PIS criado com sucesso.")
            return redirect("fiscal:lista_csts_pis")

    return render(
        request,
        "fiscal/cst_pis/form.html",
        {
            "form": form,
            "titulo": "Novo CST PIS",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_cst_pis_view(request, cst_pis_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    cst_pis = _obter_ou_404(cst_pis_id)
    form = CSTPISForm(request.POST or None, instance=cst_pis)

    if request.method == "POST" and form.is_valid():
        try:
            editar_cst_pis(
                cst_pis=cst_pis,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "CST PIS atualizado com sucesso.")
            return redirect("fiscal:lista_csts_pis")

    return render(
        request,
        "fiscal/cst_pis/form.html",
        {
            "form": form,
            "titulo": "Editar CST PIS",
            "cst_pis": cst_pis,
        },
    )
