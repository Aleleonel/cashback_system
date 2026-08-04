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
from fiscal.forms import CSTCOFINSForm
from fiscal.models import CSTCOFINS
from fiscal.selectors import get_cst_cofins, get_csts_cofins
from fiscal.services import criar_cst_cofins, editar_cst_cofins


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


def _obter_ou_404(cst_cofins_id):
    try:
        return get_cst_cofins(cst_cofins_id=cst_cofins_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CST COFINS nao encontrado.") from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_csts_cofins(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"
    tipo_operacao = request.GET.get("tipo_operacao", "").strip()

    pagina = Paginator(
        get_csts_cofins(
            busca=busca,
            somente_ativos=somente_ativos,
            tipo_operacao=tipo_operacao,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/cst_cofins/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "somente_ativos": somente_ativos,
            "tipo_operacao": tipo_operacao,
            "tipos_operacao": CSTCOFINS.TIPO_OPERACAO_CHOICES,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_cst_cofins_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CSTCOFINSForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_cst_cofins(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "CST COFINS criado com sucesso.")
            return redirect("fiscal:lista_csts_cofins")

    return render(
        request,
        "fiscal/cst_cofins/form.html",
        {
            "form": form,
            "titulo": "Novo CST COFINS",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_cst_cofins_view(request, cst_cofins_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    cst_cofins = _obter_ou_404(cst_cofins_id)
    form = CSTCOFINSForm(request.POST or None, instance=cst_cofins)

    if request.method == "POST" and form.is_valid():
        try:
            editar_cst_cofins(
                cst_cofins=cst_cofins,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "CST COFINS atualizado com sucesso.")
            return redirect("fiscal:lista_csts_cofins")

    return render(
        request,
        "fiscal/cst_cofins/form.html",
        {
            "form": form,
            "titulo": "Editar CST COFINS",
            "cst_cofins": cst_cofins,
        },
    )
