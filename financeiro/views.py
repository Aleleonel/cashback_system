import uuid
from calendar import monthrange
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.services import usuario_tem_permissao
from accounts.models import Usuario
from accounts.permissions import (
    PERMISSAO_FINANCEIRO_BAIXAR,
    PERMISSAO_FINANCEIRO_GERENCIAR,
    PERMISSAO_FINANCEIRO_LANCAR_DESPESA,
    PERMISSAO_FINANCEIRO_VISUALIZAR,
)
from empresas.models import Loja
from financeiro.models import BaixaFinanceira, CentroCusto, ContaFinanceira, InstituicaoBancaria, PlanoConta, TituloFinanceiro
from financeiro.services import criar_lancamento_manual
from financeiro.forms import BaixaDinheiroForm, CentroCustoForm, ContaFinanceiraForm, InstituicaoBancariaForm, LancamentoManualForm, PlanoContaForm
from financeiro.selectors import ESCOPO_CONSOLIDADO, ESCOPO_LOJA, ESCOPO_MATRIZ, listar_titulos, resumo_saldos


def _matriz_usuario(request):
    matriz = getattr(request.user, "matriz", None)
    if matriz is None:
        raise Http404("Usuario sem matriz vinculada.")
    return matriz


def _lojas_autorizadas(request, matriz):
    if request.user.perfil == Usuario.PERFIL_MASTER:
        return Loja.objects.filter(matriz=matriz).order_by("nome")
    return request.user.lojas.filter(matriz=matriz).order_by("nome")


def _resolver_escopo(request, matriz):
    lojas = _lojas_autorizadas(request, matriz)
    escopo = (request.GET.get("escopo") or "").strip().lower()
    loja_id = (request.GET.get("loja") or "").strip()
    if request.user.perfil == Usuario.PERFIL_MASTER:
        if not escopo:
            escopo = ESCOPO_CONSOLIDADO
        if escopo in {ESCOPO_CONSOLIDADO, ESCOPO_MATRIZ}:
            return escopo, None, lojas
        if escopo == ESCOPO_LOJA:
            if not loja_id:
                raise Http404("Selecione uma loja.")
            return escopo, get_object_or_404(lojas, pk=loja_id), lojas
        raise Http404("Escopo financeiro invalido.")
    if request.user.perfil == Usuario.PERFIL_ADMIN_LOJA:
        if not lojas.exists():
            raise Http404("Usuario sem loja autorizada.")
        loja = get_object_or_404(lojas, pk=loja_id) if loja_id else lojas.first()
        return ESCOPO_LOJA, loja, lojas
    if request.user.perfil == Usuario.PERFIL_OPERADOR:
        if not lojas.exists():
            raise Http404("Usuario sem loja autorizada.")
        loja = get_object_or_404(lojas, pk=loja_id) if loja_id else lojas.first()
        return ESCOPO_LOJA, loja, lojas
    return None, None, lojas


def _contexto_financeiro(request):
    matriz = _matriz_usuario(request)
    escopo, loja, lojas = _resolver_escopo(request, matriz)
    if escopo is None:
        return None
    natureza = (request.GET.get("natureza") or "").strip().upper()
    status = (request.GET.get("status") or "").strip().upper()
    if natureza not in {TituloFinanceiro.Natureza.PAGAR, TituloFinanceiro.Natureza.RECEBER}:
        natureza = None
    if status not in {TituloFinanceiro.Status.ABERTO, TituloFinanceiro.Status.PARCIAL, TituloFinanceiro.Status.LIQUIDADO, TituloFinanceiro.Status.CANCELADO}:
        status = None
    saldos = resumo_saldos(matriz=matriz, escopo=escopo, loja=loja)
    queryset = listar_titulos(matriz=matriz, natureza=natureza, status=status, escopo=escopo, loja=loja)
    pagina = Paginator(queryset, 20).get_page(request.GET.get("page"))
    return {
        "matriz": matriz,
        "lojas": lojas,
        "escopo": escopo,
        "loja": loja,
        "natureza": natureza or "",
        "status": status or "",
        "saldos": saldos,
        "saldo_liquido": saldos["receber"] - saldos["pagar"],
        "pagina": pagina,
    }


@login_required
@require_permission(PERMISSAO_FINANCEIRO_VISUALIZAR)
def painel(request):
    contexto = _contexto_financeiro(request)
    if contexto is None:
        return HttpResponseForbidden("Usuario sem acesso ao Financeiro.")
    return render(request, "financeiro/painel.html", contexto)


@login_required
@require_permission(PERMISSAO_FINANCEIRO_VISUALIZAR)
def titulos(request):
    contexto = _contexto_financeiro(request)
    if contexto is None:
        return HttpResponseForbidden("Usuario sem acesso ao Financeiro.")
    return render(request, "financeiro/titulos.html", contexto)


@login_required
@require_permission(PERMISSAO_FINANCEIRO_VISUALIZAR)
def titulo_detalhe(request, titulo_uuid):
    matriz = _matriz_usuario(request)
    escopo, loja, lojas = _resolver_escopo(request, matriz)
    if escopo is None:
        return HttpResponseForbidden("Usuario sem acesso ao Financeiro.")
    queryset = TituloFinanceiro.objects.filter(matriz=matriz).select_related("loja")
    if escopo == ESCOPO_MATRIZ:
        queryset = queryset.filter(loja__isnull=True)
    elif escopo == ESCOPO_LOJA:
        queryset = queryset.filter(loja=loja)
    titulo = get_object_or_404(queryset, uuid=titulo_uuid)
    parcelas = titulo.parcelas.all().prefetch_related("baixas").order_by("numero")
    return render(request, "financeiro/titulo_detalhe.html", {
        "matriz": matriz, "lojas": lojas, "escopo": escopo, "loja": loja,
        "titulo": titulo, "parcelas": parcelas,
    })

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def planos_conta(request):
    matriz = _matriz_usuario(request)
    planos = (
        PlanoConta.objects.filter(matriz=matriz)
        .select_related("pai")
        .order_by("codigo", "nome")
    )
    return render(
        request,
        "financeiro/planos_conta.html",
        {
            "matriz": matriz,
            "planos": planos,
        },
    )


@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def plano_conta_novo(request):
    matriz = _matriz_usuario(request)

    if request.method == "POST":
        form = PlanoContaForm(request.POST)
        if form.is_valid():
            plano = form.save(commit=False)
            plano.matriz = matriz
            plano.save()
            return redirect("financeiro:planos_conta")
    else:
        form = PlanoContaForm()

    form.fields["pai"].queryset = (
        PlanoConta.objects.filter(matriz=matriz, ativo=True)
        .order_by("codigo", "nome")
    )

    return render(
        request,
        "financeiro/plano_conta_form.html",
        {
            "matriz": matriz,
            "form": form,
        },
    )

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def centros_custo(request):
    matriz = _matriz_usuario(request)
    centros = CentroCusto.objects.filter(matriz=matriz).order_by("codigo", "nome")
    return render(
        request,
        "financeiro/centros_custo.html",
        {
            "matriz": matriz,
            "centros": centros,
        },
    )


@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def plano_conta_editar(request, plano_uuid):
    matriz = _matriz_usuario(request)
    try:
        plano = PlanoConta.objects.get(uuid=plano_uuid, matriz=matriz)
    except PlanoConta.DoesNotExist as exc:
        raise Http404("Plano de contas nao encontrado.") from exc

    if request.method == "POST":
        form = PlanoContaForm(request.POST, instance=plano)
    else:
        form = PlanoContaForm(instance=plano)

    form.fields["pai"].queryset = (
        PlanoConta.objects.filter(matriz=matriz, ativo=True)
        .exclude(pk=plano.pk)
        .order_by("codigo", "nome")
    )

    if request.method == "POST" and form.is_valid():
        atualizado = form.save(commit=False)
        if atualizado.tipo == PlanoConta.Tipo.SINTETICA:
            atualizado.aceita_lancamento = False
        atualizado.matriz = matriz
        atualizado.save()
        return redirect("financeiro:planos_conta")

    return render(
        request,
        "financeiro/plano_conta_form.html",
        {"matriz": matriz, "form": form, "modo_edicao": True, "plano": plano},
    )

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def centro_custo_novo(request):
    matriz = _matriz_usuario(request)

    if request.method == "POST":
        form = CentroCustoForm(request.POST)
        if form.is_valid():
            centro = form.save(commit=False)
            centro.matriz = matriz
            centro.save()
            return redirect("financeiro:centros_custo")
    else:
        form = CentroCustoForm()

    return render(
        request,
        "financeiro/centro_custo_form.html",
        {
            "matriz": matriz,
            "form": form,
        },
    )

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def instituicoes_bancarias(request):
    instituicoes = InstituicaoBancaria.objects.all().order_by("nome", "codigo_bacen")
    return render(
        request,
        "financeiro/instituicoes_bancarias.html",
        {"instituicoes": instituicoes},
    )


@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def instituicao_bancaria_nova(request):
    if request.method == "POST":
        form = InstituicaoBancariaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("financeiro:instituicoes_bancarias")
    else:
        form = InstituicaoBancariaForm()

    return render(
        request,
        "financeiro/instituicao_bancaria_form.html",
        {"form": form},
    )

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def contas_financeiras(request):
    matriz = _matriz_usuario(request)
    contas = (
        ContaFinanceira.objects.filter(matriz=matriz)
        .select_related("loja", "instituicao")
        .order_by("nome")
    )
    return render(
        request,
        "financeiro/contas_financeiras.html",
        {"matriz": matriz, "contas": contas},
    )


@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def conta_financeira_nova(request):
    matriz = _matriz_usuario(request)
    if request.method == "POST":
        form = ContaFinanceiraForm(request.POST)
    else:
        form = ContaFinanceiraForm()

    form.fields["loja"].queryset = _lojas_autorizadas(request, matriz)
    form.fields["instituicao"].queryset = InstituicaoBancaria.objects.all().order_by("nome")

    if request.method == "POST" and form.is_valid():
        conta = form.save(commit=False)
        conta.matriz = matriz
        conta.save()
        return redirect("financeiro:contas_financeiras")

    return render(
        request,
        "financeiro/conta_financeira_form.html",
        {"matriz": matriz, "form": form},
    )

def _somar_meses(data_base, meses):
    indice = data_base.month - 1 + meses
    ano = data_base.year + indice // 12
    mes = indice % 12 + 1
    dia = min(data_base.day, monthrange(ano, mes)[1])
    return data_base.replace(year=ano, month=mes, day=dia)


def _gerar_parcelas_lancamento_manual(valor_final, quantidade, primeiro_vencimento):
    centavos = int(valor_final * 100)
    base = centavos // quantidade
    resto = centavos % quantidade
    parcelas = []
    for indice in range(quantidade):
        valor_centavos = base + (1 if indice < resto else 0)
        parcelas.append({
            "numero": indice + 1,
            "vencimento": _somar_meses(primeiro_vencimento, indice),
            "valor": (Decimal(valor_centavos) / Decimal("100")).quantize(Decimal("0.01")),
        })
    return parcelas


@login_required
@require_permission(PERMISSAO_FINANCEIRO_LANCAR_DESPESA)
def lancamento_manual(request):
    matriz = _matriz_usuario(request)
    lojas = _lojas_autorizadas(request, matriz)
    form = LancamentoManualForm(
        request.POST if request.method == "POST" else None,
        matriz=matriz,
        lojas=lojas,
    )
    pode_gerenciar_financeiro = usuario_tem_permissao(request.user, PERMISSAO_FINANCEIRO_GERENCIAR)
    if not pode_gerenciar_financeiro:
        form.fields["natureza"].choices = [
            (TituloFinanceiro.Natureza.PAGAR, TituloFinanceiro.Natureza.PAGAR.label),
        ]

    if request.method == "POST" and form.is_valid():
        dados = form.cleaned_data
        if not pode_gerenciar_financeiro:
            dados["natureza"] = TituloFinanceiro.Natureza.PAGAR
        valor_final = dados["valor_final"]
        parcelas = _gerar_parcelas_lancamento_manual(
            valor_final,
            dados["numero_parcelas"],
            dados["data_vencimento"],
        )
        token_idempotencia = (request.POST.get("chave_idempotencia") or "").strip()
        try:
            token_idempotencia = str(uuid.UUID(token_idempotencia))
        except (ValueError, TypeError, AttributeError):
            form.add_error(None, "Token de idempotencia invalido. Recarregue o formulario.")
            return render(
                request,
                "financeiro/lancamento_manual.html",
                {"matriz": matriz, "form": form, "chave_idempotencia": token_idempotencia},
            )
        chave_idempotencia = f"manual-ui:{matriz.pk}:{request.user.pk}:{token_idempotencia}"
        descricao = dados["entidade_nome"] or dados["documento_referencia"] or "Lancamento manual"

        try:
            titulo = criar_lancamento_manual(
                matriz=matriz,
                loja=dados["loja"],
                natureza=dados["natureza"],
                chave_idempotencia=chave_idempotencia,
                descricao=descricao,
                data_emissao=dados["data_emissao"],
                parcelas=parcelas,
                plano_conta=dados["plano_conta"],
                centro_custo=dados["centro_custo"],
                entidade_nome=dados["entidade_nome"],
                documento_referencia=dados["documento_referencia"],
                data_competencia=dados["data_competencia"],
                valor_bruto=dados["valor_bruto"],
                valor_desconto=dados["valor_desconto"] or Decimal("0.00"),
                valor_juros=dados["valor_juros"] or Decimal("0.00"),
                observacao=dados["observacao"],
                usuario=request.user,
                request=request,
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                for campo, mensagens in exc.message_dict.items():
                    destino = campo if campo in form.fields else None
                    for mensagem in mensagens:
                        form.add_error(destino, mensagem)
            else:
                for mensagem in exc.messages:
                    form.add_error(None, mensagem)
        else:
            return redirect("financeiro:titulo_detalhe", titulo_uuid=titulo.uuid)

    chave_idempotencia = (
        (request.POST.get("chave_idempotencia") or "").strip()
        if request.method == "POST"
        else str(uuid.uuid4())
    )
    return render(
        request,
        "financeiro/lancamento_manual.html",
        {"matriz": matriz, "form": form, "chave_idempotencia": chave_idempotencia},
    )

@login_required
@require_permission(PERMISSAO_FINANCEIRO_BAIXAR)
def parcela_baixa_nova(request, titulo_uuid, parcela_id):
    from django.db.models import Q
    from django.utils import timezone
    from pdv.choices import StatusSessaoCaixa, TipoFormaPagamento
    from pdv.models import FormaPagamento, SessaoCaixa
    from financeiro.services import registrar_baixa_financeira_com_caixa

    matriz = _matriz_usuario(request)
    titulo = get_object_or_404(TituloFinanceiro, matriz=matriz, uuid=titulo_uuid)
    lojas = _lojas_autorizadas(request, matriz)
    if titulo.loja_id is None or not lojas.filter(pk=titulo.loja_id).exists():
        raise Http404("Titulo sem loja autorizada para baixa.")
    parcela = get_object_or_404(titulo.parcelas.all(), pk=parcela_id)
    formas_pagamento = FormaPagamento.objects.filter(matriz=matriz, ativa=True).order_by("nome")
    contas_financeiras = ContaFinanceira.objects.filter(matriz=matriz, ativo=True).filter(
        Q(loja__isnull=True) | Q(loja=titulo.loja)
    ).order_by("nome")
    form_kwargs = {"formas_pagamento": formas_pagamento, "contas_financeiras": contas_financeiras}
    sessoes = SessaoCaixa.objects.filter(
        caixa__matriz=matriz, caixa__loja=titulo.loja, status=StatusSessaoCaixa.ABERTA
    ).select_related("caixa")

    if request.method == "POST":
        form = BaixaDinheiroForm(request.POST, **form_kwargs)
        token_idempotencia = (request.POST.get("chave_idempotencia") or "").strip()
        try:
            token_idempotencia = str(uuid.UUID(token_idempotencia))
        except (ValueError, AttributeError, TypeError):
            form.add_error(None, "Token de idempotencia invalido. Recarregue o formulario.")
        if form.is_valid() and not form.non_field_errors():
            forma = form.cleaned_data["forma_pagamento"]
            conta = form.cleaned_data["conta_financeira"]
            dinheiro = forma.tipo == TipoFormaPagamento.DINHEIRO
            sessao = sessoes.filter(operador_abertura=request.user).first() if dinheiro else None
            if dinheiro and sessao is None:
                form.add_error(None, "Nao existe sessao de caixa aberta por este usuario nesta loja.")
            elif not dinheiro and conta is None:
                form.add_error("conta_financeira", "Conta financeira e obrigatoria para baixa nao-dinheiro.")
            else:
                try:
                    registrar_baixa_financeira_com_caixa(
                        parcela=parcela, valor=form.cleaned_data["valor"], data=form.cleaned_data["data"],
                        chave_idempotencia=f"baixa-ui:{matriz.pk}:{request.user.pk}:{token_idempotencia}",
                        forma_pagamento=forma, conta_financeira=conta, sessao_caixa=sessao,
                        operador=request.user if dinheiro else None,
                        observacao=form.cleaned_data["observacao"], usuario=request.user, request=request,
                    )
                except ValidationError as exc:
                    if hasattr(exc, "message_dict"):
                        for campo, mensagens in exc.message_dict.items():
                            for mensagem in mensagens:
                                form.add_error(campo if campo in form.fields else None, mensagem)
                    else:
                        for mensagem in exc.messages:
                            form.add_error(None, mensagem)
                else:
                    return redirect("financeiro:titulo_detalhe", titulo_uuid=titulo.uuid)
    else:
        token_idempotencia = str(uuid.uuid4())
        total_baixas = sum((e.valor for e in parcela.baixas.all() if e.tipo == BaixaFinanceira.Tipo.BAIXA), Decimal("0.00"))
        total_estornos = sum((e.valor for e in parcela.baixas.all() if e.tipo == BaixaFinanceira.Tipo.ESTORNO), Decimal("0.00"))
        saldo_parcela = parcela.valor_original - total_baixas + total_estornos
        initial = {"valor": saldo_parcela, "data": timezone.localdate()}
        dinheiro = formas_pagamento.filter(tipo=TipoFormaPagamento.DINHEIRO)
        if dinheiro.count() == 1:
            initial["forma_pagamento"] = dinheiro.get()
        form = BaixaDinheiroForm(initial=initial, **form_kwargs)
    return render(request, "financeiro/parcela_baixa_form.html", {
        "titulo": titulo, "parcela": parcela, "form": form, "chave_idempotencia": token_idempotencia,
    })
