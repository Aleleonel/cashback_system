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
from fiscal.forms import RegraFiscalForm
from fiscal.models import RegraFiscal
from fiscal.selectors import (
    get_regra_fiscal,
    get_regras_fiscais,
)
from fiscal.services import (
    criar_regra_fiscal,
    editar_regra_fiscal,
)


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


def _obter_ou_404(regra_id):
    try:
        return get_regra_fiscal(regra_id=regra_id)
    except ObjectDoesNotExist as erro:
        raise Http404(
            "Regra fiscal nao encontrada."
        ) from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_regras_fiscais(request):
    busca = request.GET.get("busca", "").strip()
    regime = request.GET.get(
        "regime_tributario",
        "",
    ).strip()
    tipo = request.GET.get(
        "tipo_operacao",
        "",
    ).strip()
    finalidade = request.GET.get(
        "finalidade_operacao",
        "",
    ).strip()
    uf_origem = request.GET.get(
        "uf_origem",
        "",
    ).strip()
    uf_destino = request.GET.get(
        "uf_destino",
        "",
    ).strip()
    somente_ativas = request.GET.get("ativas") == "1"

    pagina = Paginator(
        get_regras_fiscais(
            busca=busca,
            somente_ativas=somente_ativas,
            regime_tributario=regime,
            tipo_operacao=tipo,
            finalidade_operacao=finalidade,
            uf_origem=uf_origem,
            uf_destino=uf_destino,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/regra_fiscal/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "regime_tributario": regime,
            "tipo_operacao": tipo,
            "finalidade_operacao": finalidade,
            "uf_origem": uf_origem,
            "uf_destino": uf_destino,
            "somente_ativas": somente_ativas,
            "regimes": (
                RegraFiscal.REGIME_TRIBUTARIO_CHOICES
            ),
            "tipos": (
                RegraFiscal.TIPO_OPERACAO_CHOICES
            ),
            "finalidades": (
                RegraFiscal.FINALIDADE_OPERACAO_CHOICES
            ),
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_regra_fiscal_view(request):
    form = RegraFiscalForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_regra_fiscal(
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz_auditoria=getattr(
                    request.user,
                    "matriz",
                    None,
                ),
                loja_auditoria=getattr(
                    request.user,
                    "loja",
                    None,
                ),
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(
                request,
                "Regra fiscal criada com sucesso.",
            )
            return redirect(
                "fiscal:lista_regras_fiscais"
            )

    return render(
        request,
        "fiscal/regra_fiscal/form.html",
        {
            "form": form,
            "titulo": "Nova regra fiscal",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_regra_fiscal_view(request, regra_id):
    regra = _obter_ou_404(regra_id)
    form = RegraFiscalForm(
        request.POST or None,
        instance=regra,
    )

    if request.method == "POST" and form.is_valid():
        try:
            editar_regra_fiscal(
                regra=regra,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                matriz_auditoria=getattr(
                    request.user,
                    "matriz",
                    None,
                ),
                loja_auditoria=getattr(
                    request.user,
                    "loja",
                    None,
                ),
                request=request,
            )
        except ValidationError as erro:
            _aplicar_erros(form, erro)
        else:
            messages.success(
                request,
                "Regra fiscal atualizada com sucesso.",
            )
            return redirect(
                "fiscal:lista_regras_fiscais"
            )

    return render(
        request,
        "fiscal/regra_fiscal/form.html",
        {
            "form": form,
            "titulo": "Editar regra fiscal",
            "regra": regra,
        },
    )
