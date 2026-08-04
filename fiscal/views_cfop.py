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
from fiscal.forms import CFOPForm
from fiscal.models import CFOP
from fiscal.selectors import get_cfop, get_cfops
from fiscal.services import criar_cfop, editar_cfop


def _erros(form, erro):
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in erro.messages:
            form.add_error(None, mensagem)


def _get(cfop_id):
    try:
        return get_cfop(cfop_id=cfop_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CFOP nao encontrado.") from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_cfops(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"
    tipo_operacao = request.GET.get("tipo_operacao", "").strip()
    destino_operacao = request.GET.get("destino_operacao", "").strip()

    pagina = Paginator(
        get_cfops(
            busca=busca,
            somente_ativos=somente_ativos,
            tipo_operacao=tipo_operacao,
            destino_operacao=destino_operacao,
        ),
        25,
    ).get_page(request.GET.get("page"))

    return render(request, "fiscal/cfop/lista.html", {
        "pagina": pagina,
        "busca": busca,
        "somente_ativos": somente_ativos,
        "tipo_operacao": tipo_operacao,
        "destino_operacao": destino_operacao,
        "tipos_operacao": CFOP.TIPO_OPERACAO_CHOICES,
        "destinos_operacao": CFOP.DESTINO_OPERACAO_CHOICES,
    })


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_cfop_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CFOPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_cfop(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _erros(form, erro)
        else:
            messages.success(request, "CFOP criado com sucesso.")
            return redirect("fiscal:lista_cfops")

    return render(request, "fiscal/cfop/form.html", {
        "form": form,
        "titulo": "Novo CFOP",
    })


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_cfop_view(request, cfop_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    cfop = _get(cfop_id)
    form = CFOPForm(request.POST or None, instance=cfop)

    if request.method == "POST" and form.is_valid():
        try:
            editar_cfop(
                cfop=cfop,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz=matriz,
                loja=loja,
                request=request,
            )
        except ValidationError as erro:
            _erros(form, erro)
        else:
            messages.success(request, "CFOP atualizado com sucesso.")
            return redirect("fiscal:lista_cfops")

    return render(request, "fiscal/cfop/form.html", {
        "form": form,
        "titulo": "Editar CFOP",
        "cfop": cfop,
    })
