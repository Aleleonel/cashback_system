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
from fiscal.forms import BeneficioFiscalForm
from fiscal.models import BeneficioFiscal
from fiscal.selectors import (
    get_beneficio_fiscal,
    get_beneficios_fiscais,
)
from fiscal.services import (
    criar_beneficio_fiscal,
    editar_beneficio_fiscal,
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


def _obter_ou_404(beneficio_id):
    try:
        return get_beneficio_fiscal(
            beneficio_id=beneficio_id
        )
    except ObjectDoesNotExist as erro:
        raise Http404(
            "Beneficio fiscal nao encontrado."
        ) from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_beneficios_fiscais(request):
    busca = request.GET.get("busca", "").strip()
    uf = request.GET.get("uf", "").strip().upper()
    tipo_beneficio = request.GET.get(
        "tipo_beneficio",
        "",
    ).strip()
    regime_tributario = request.GET.get(
        "regime_tributario",
        "",
    ).strip()
    somente_ativos = request.GET.get("ativos") == "1"

    pagina = Paginator(
        get_beneficios_fiscais(
            busca=busca,
            uf=uf,
            tipo_beneficio=tipo_beneficio,
            regime_tributario=regime_tributario,
            somente_ativos=somente_ativos,
        ),
        50,
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "fiscal/beneficio_fiscal/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "uf": uf,
            "tipo_beneficio": tipo_beneficio,
            "regime_tributario": regime_tributario,
            "somente_ativos": somente_ativos,
            "tipos_beneficio": (
                BeneficioFiscal.TIPO_BENEFICIO_CHOICES
            ),
            "regimes_tributarios": (
                BeneficioFiscal.REGIME_TRIBUTARIO_CHOICES
            ),
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_beneficio_fiscal_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    form = BeneficioFiscalForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            criar_beneficio_fiscal(
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
                "Beneficio fiscal criado com sucesso.",
            )
            return redirect(
                "fiscal:lista_beneficios_fiscais"
            )

    return render(
        request,
        "fiscal/beneficio_fiscal/form.html",
        {
            "form": form,
            "titulo": "Novo beneficio fiscal",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_beneficio_fiscal_view(
    request,
    beneficio_id,
):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    beneficio = _obter_ou_404(beneficio_id)
    form = BeneficioFiscalForm(
        request.POST or None,
        instance=beneficio,
    )

    if request.method == "POST" and form.is_valid():
        try:
            editar_beneficio_fiscal(
                beneficio=beneficio,
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
                "Beneficio fiscal atualizado com sucesso.",
            )
            return redirect(
                "fiscal:lista_beneficios_fiscais"
            )

    return render(
        request,
        "fiscal/beneficio_fiscal/form.html",
        {
            "form": form,
            "titulo": "Editar beneficio fiscal",
            "beneficio": beneficio,
        },
    )
