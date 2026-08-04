from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from accounts.decorators import require_permission
from fiscal.constants import PERMISSAO_FISCAL_GERENCIAR_CADASTROS, PERMISSAO_FISCAL_VISUALIZAR
from fiscal.forms import CSOSNForm
from fiscal.selectors import get_csosn, get_csosns
from fiscal.services import criar_csosn, editar_csosn

def _erros(form, erro):
    if hasattr(erro, "message_dict"):
        for campo, mensagens in erro.message_dict.items():
            for mensagem in mensagens:
                form.add_error(campo if campo in form.fields else None, mensagem)
    else:
        for mensagem in erro.messages:
            form.add_error(None, mensagem)

def _get(csosn_id):
    try:
        return get_csosn(csosn_id=csosn_id)
    except ObjectDoesNotExist as erro:
        raise Http404("CSOSN nao encontrado.") from erro

@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_csosns(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativos = request.GET.get("ativos") == "1"
    pagina = Paginator(get_csosns(busca=busca, somente_ativos=somente_ativos), 25).get_page(request.GET.get("page"))
    return render(request, "fiscal/csosn/lista.html", {"pagina": pagina, "busca": busca, "somente_ativos": somente_ativos})

@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_csosn_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = CSOSNForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            criar_csosn(dados=form.cleaned_data, usuario_executor=request.user, matriz=matriz, loja=loja, request=request)
        except ValidationError as erro:
            _erros(form, erro)
        else:
            messages.success(request, "CSOSN criado com sucesso.")
            return redirect("fiscal:lista_csosns")
    return render(request, "fiscal/csosn/form.html", {"form": form, "titulo": "Novo CSOSN"})

@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_csosn_view(request, csosn_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    csosn = _get(csosn_id)
    form = CSOSNForm(request.POST or None, instance=csosn)
    if request.method == "POST" and form.is_valid():
        try:
            editar_csosn(csosn=csosn, dados=form.cleaned_data, usuario_executor=request.user, matriz=matriz, loja=loja, request=request)
        except ValidationError as erro:
            _erros(form, erro)
        else:
            messages.success(request, "CSOSN atualizado com sucesso.")
            return redirect("fiscal:lista_csosns")
    return render(request, "fiscal/csosn/form.html", {"form": form, "titulo": "Editar CSOSN", "csosn": csosn})
