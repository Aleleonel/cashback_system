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
from fiscal.forms import CSTIPIForm
from fiscal.models import CSTIPI
from fiscal.selectors import get_cst_ipi, get_csts_ipi
from fiscal.services import criar_cst_ipi, editar_cst_ipi


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


def _obter_ou_404(cst_ipi_id):
    try:
        return get_cst_ipi(cst_ipi_id=cst_ipi_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CST IPI nao encontrado.") from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_csts_ipi(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"
    tipo_operacao = request.GET.get("tipo_operacao", "").strip()

    pagina = Paginator(
        get_csts_ipi(
            busca=busca,
            somente_ativos=somente_ativos,
            tipo_operacao=tipo_operacao,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/cst_ipi/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "somente_ativos": somente_ativos,
            "tipo_operacao": tipo_operacao,
            "tipos_operacao": CSTIPI.TIPO_OPERACAO_CHOICES,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_cst_ipi_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CSTIPIForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_cst_ipi(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "CST IPI criado com sucesso.")
            return redirect("fiscal:lista_csts_ipi")

    return render(
        request,
        "fiscal/cst_ipi/form.html",
        {
            "form": form,
            "titulo": "Novo CST IPI",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_cst_ipi_view(request, cst_ipi_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    cst_ipi = _obter_ou_404(cst_ipi_id)
    form = CSTIPIForm(request.POST or None, instance=cst_ipi)

    if request.method == "POST" and form.is_valid():
        try:
            editar_cst_ipi(
                cst_ipi=cst_ipi,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(request, "CST IPI atualizado com sucesso.")
            return redirect("fiscal:lista_csts_ipi")

    return render(
        request,
        "fiscal/cst_ipi/form.html",
        {
            "form": form,
            "titulo": "Editar CST IPI",
            "cst_ipi": cst_ipi,
        },
    )
