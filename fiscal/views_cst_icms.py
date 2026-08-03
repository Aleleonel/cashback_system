from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from accounts.decorators import require_permission
from fiscal.constants import PERMISSAO_FISCAL_GERENCIAR_CADASTROS, PERMISSAO_FISCAL_VISUALIZAR
from fiscal.forms import CSTICMSForm
from fiscal.selectors import get_cst_icms, get_csts_icms
from fiscal.services import criar_cst_icms, editar_cst_icms

def _erros(form, erro):
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in erro.messages:
            form.add_error(None, mensagem)

def _get(cst_id):
    try:
        return get_cst_icms(cst_id=cst_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CST ICMS nao encontrado.") from erro

@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_csts_icms(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"
    pagina = Paginator(get_csts_icms(busca=busca, somente_ativos=somente_ativos), 25).get_page(request.GET.get("page"))
    return render(request, "fiscal/cst_icms/lista.html", {"pagina": pagina, "busca": busca, "somente_ativos": somente_ativos})

@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_cst_icms_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CSTICMSForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            criar_cst_icms(dados=form.cleaned_data, usuario_executor=request.user, matriz=matriz, loja=loja, request=request)
        except ValidationError as erro:
            _erros(form, erro)
        else:
            messages.success(request, "CST ICMS criado com sucesso.")
            return redirect("fiscal:lista_csts_icms")
    return render(request, "fiscal/cst_icms/form.html", {"form": form, "titulo": "Novo CST ICMS"})

@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_cst_icms_view(request, cst_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    cst = _get(cst_id)
    form = CSTICMSForm(request.POST or None, instance=cst)
    if request.method == "POST" and form.is_valid():
        try:
            editar_cst_icms(cst=cst, dados=form.cleaned_data, usuario_executor=request.user, matriz=matriz, loja=loja, request=request)
        except ValidationError as erro:
            _erros(form, erro)
        else:
            messages.success(request, "CST ICMS atualizado com sucesso.")
            return redirect("fiscal:lista_csts_icms")
    return render(request, "fiscal/cst_icms/form.html", {"form": form, "titulo": "Editar CST ICMS", "cst": cst})
