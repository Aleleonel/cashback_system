from datetime import date
import csv
import uuid
from calendar import monthrange
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import Http404, HttpResponseForbidden, QueryDict, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

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
from financeiro.services import cancelar_titulo_financeiro, criar_lancamento_manual
from financeiro.forms import BaixaDinheiroForm, CentroCustoForm, ContaFinanceiraForm, EstornoBaixaForm, InstituicaoBancariaForm, LancamentoManualForm, PlanoContaForm
from financeiro.importacao_csv import importar_titulos_csv
from financeiro.selectors import ESCOPO_CONSOLIDADO, ESCOPO_LOJA, ESCOPO_MATRIZ, listar_titulos, resumo_fluxo_caixa, resumo_saldos


def _matriz_usuario(request):
    matriz = getattr(request.user, "matriz", None)
    if matriz is None:
        raise Http404("Usuario sem matriz vinculada.")
    return matriz


def _lojas_autorizadas(request, matriz):
    if request.user.perfil == Usuario.PERFIL_MASTER:
        return Loja.objects.filter(matriz=matriz).order_by("nome")
    return request.user.lojas.filter(matriz=matriz).order_by("nome")


def _lojas_relatorio(request, matriz):
    if request.user.perfil == Usuario.PERFIL_OPERADOR:
        return request.user.lojas.filter(matriz=matriz).order_by("nome")
    return Loja.objects.filter(matriz=matriz).order_by("nome")


def _resolver_escopo_relatorio(request, matriz):
    lojas = _lojas_relatorio(request, matriz)
    loja_id = (request.GET.get("loja") or "").strip()
    if request.user.perfil == Usuario.PERFIL_OPERADOR:
        if not lojas.exists():
            raise Http404("Usuario sem loja autorizada.")
        session = getattr(request, "session", None)
        loja_operacional_id = session.get("loja_operacional_id") if session is not None else None
        loja = lojas.filter(pk=loja_operacional_id).first() if loja_operacional_id is not None else None
        if loja is None:
            loja = lojas.first()
            if session is not None:
                session["loja_operacional_id"] = loja.pk
        return ESCOPO_LOJA, loja, lojas
    if loja_id:
        return ESCOPO_LOJA, get_object_or_404(lojas, pk=loja_id), lojas
    return ESCOPO_CONSOLIDADO, None, lojas


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
        usuario_operacional = True
        pode_filtrar_loja = False
        session = getattr(request, "session", None)
        loja_operacional_id = session.get("loja_operacional_id") if session is not None else None
        loja = lojas.filter(pk=loja_operacional_id).first() if loja_operacional_id is not None else None
        if loja is None:
            loja = lojas.first()
            if session is not None:
                session["loja_operacional_id"] = loja.pk
        return ESCOPO_LOJA, loja, lojas
    return None, None, lojas


def _contexto_financeiro(request, modo_relatorio=False):
    matriz = _matriz_usuario(request)
    if modo_relatorio:
        escopo, loja, lojas = _resolver_escopo_relatorio(request, matriz)
    else:
        escopo, loja, lojas = _resolver_escopo(request, matriz)
    if escopo is None:
        return None
    usuario_operacional = request.user.perfil == Usuario.PERFIL_OPERADOR
    pode_filtrar_loja = not usuario_operacional
    natureza = (request.GET.get("natureza") or "").strip().upper()
    status = (request.GET.get("status") or "").strip().upper()
    if natureza not in {TituloFinanceiro.Natureza.PAGAR, TituloFinanceiro.Natureza.RECEBER}:
        natureza = None
    if status not in {TituloFinanceiro.Status.ABERTO, TituloFinanceiro.Status.PARCIAL, TituloFinanceiro.Status.LIQUIDADO, TituloFinanceiro.Status.CANCELADO}:
        status = None
    hoje = timezone.localdate()
    data_inicio_raw = (request.GET.get("data_inicio") or "").strip()
    data_fim_raw = (request.GET.get("data_fim") or "").strip()
    try:
        data_inicio = date.fromisoformat(data_inicio_raw) if data_inicio_raw else hoje.replace(day=1)
    except ValueError:
        data_inicio = hoje.replace(day=1)
    try:
        data_fim = date.fromisoformat(data_fim_raw) if data_fim_raw else hoje.replace(day=monthrange(hoje.year, hoje.month)[1])
    except ValueError:
        data_fim = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])
    fluxo_caixa = resumo_fluxo_caixa(
        matriz=matriz, data_inicio=data_inicio, data_fim=data_fim, escopo=escopo, loja=loja,
    )
    saldos = resumo_saldos(matriz=matriz, escopo=escopo, loja=loja)
    queryset = listar_titulos(matriz=matriz, natureza=natureza, status=status, escopo=escopo, loja=loja)
    pagina = Paginator(queryset, 20).get_page(request.GET.get("page"))
    return {
        "matriz": matriz,
        "lojas": lojas,
        "escopo": escopo,
        "loja": loja,
        "usuario_operacional": usuario_operacional,
        "pode_filtrar_loja": pode_filtrar_loja,
        "loja_operacional": loja if usuario_operacional else None,
        "modo_relatorio": modo_relatorio,
        "natureza": natureza or "",
        "status": status or "",
        "saldos": saldos,
        "saldo_liquido": saldos["receber"] - saldos["pagar"],
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "fluxo_caixa": fluxo_caixa,
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
def painel_relatorio(request):
    contexto = _contexto_financeiro(request, modo_relatorio=True)
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
def titulos_exportar_csv(request):
    matriz = _matriz_usuario(request)
    escopo, loja, lojas = _resolver_escopo(request, matriz)
    if escopo is None:
        return HttpResponseForbidden("Usuario sem acesso ao Financeiro.")

    natureza = (request.GET.get("natureza") or "").strip().upper()
    status = (request.GET.get("status") or "").strip().upper()
    if natureza not in {TituloFinanceiro.Natureza.PAGAR, TituloFinanceiro.Natureza.RECEBER}:
        natureza = None
    if status not in {
        TituloFinanceiro.Status.ABERTO,
        TituloFinanceiro.Status.PARCIAL,
        TituloFinanceiro.Status.LIQUIDADO,
        TituloFinanceiro.Status.CANCELADO,
    }:
        status = None

    titulos = listar_titulos(
        matriz=matriz,
        natureza=natureza,
        status=status,
        escopo=escopo,
        loja=loja,
    )
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="titulos_financeiros.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Emissao", "Natureza", "Descricao", "Loja", "Status", "Valor"])
    for titulo in titulos:
        writer.writerow([
            titulo.data_emissao.strftime("%d/%m/%Y"),
            titulo.get_natureza_display(),
            titulo.descricao,
            titulo.loja.nome if titulo.loja else "Matriz",
            titulo.get_status_display(),
            str(titulo.valor_original).replace(".", ","),
        ])
    return response



@login_required
@require_permission(PERMISSAO_FINANCEIRO_LANCAR_DESPESA)
def titulos_importar_csv(request):
    matriz = _matriz_usuario(request)
    escopo, loja, lojas = _resolver_escopo(request, matriz)
    if escopo is None:
        return HttpResponseForbidden("Usuario sem acesso ao Financeiro.")
    if escopo == ESCOPO_CONSOLIDADO:
        return HttpResponseForbidden("Selecione o escopo Matriz ou uma Loja para importar titulos.")

    erro = None
    resultado = None
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if arquivo is None:
            erro = "Selecione um arquivo CSV."
        else:
            try:
                resultado = importar_titulos_csv(
                    arquivo=arquivo,
                    matriz=matriz,
                    loja=loja,
                    usuario=request.user,
                    request=request,
                )
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    erro = " ".join(
                        mensagem
                        for mensagens in exc.message_dict.values()
                        for mensagem in mensagens
                    )
                else:
                    erro = " ".join(exc.messages)

    return render(
        request,
        "financeiro/titulo_importar_csv.html",
        {
            "matriz": matriz,
            "lojas": lojas,
            "escopo": escopo,
            "loja": loja,
            "erro": erro,
            "resultado": resultado,
        },
    )
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
    parcelas = titulo.parcelas.all().prefetch_related(Prefetch("baixas", queryset=BaixaFinanceira.objects.select_related("forma_pagamento", "conta_financeira"))).order_by("numero")
    return render(request, "financeiro/titulo_detalhe.html", {
        "matriz": matriz, "lojas": lojas, "escopo": escopo, "loja": loja,
        "titulo": titulo, "parcelas": parcelas,
    })

@login_required
@require_permission(PERMISSAO_FINANCEIRO_BAIXAR)
def titulo_cancelar(request, titulo_uuid):
    matriz = _matriz_usuario(request)
    escopo, loja, lojas = _resolver_escopo(request, matriz)
    if escopo is None:
        return HttpResponseForbidden("Usuario sem acesso ao Financeiro.")

    queryset = TituloFinanceiro.objects.filter(matriz=matriz)
    if escopo == ESCOPO_MATRIZ:
        queryset = queryset.filter(loja__isnull=True)
    elif escopo == ESCOPO_LOJA:
        queryset = queryset.filter(loja=loja)
    titulo = get_object_or_404(queryset, uuid=titulo_uuid)

    params = QueryDict(mutable=True)
    params["escopo"] = escopo
    if loja is not None:
        params["loja"] = str(loja.pk)
    query_escopo = params.urlencode()

    erro = None
    if request.method == "POST":
        try:
            cancelar_titulo_financeiro(
                titulo=titulo,
                usuario=request.user,
                request=request,
            )
        except ValidationError as exc:
            erro = " ".join(exc.messages)
        else:
            detalhe_url = reverse("financeiro:titulo_detalhe", kwargs={"titulo_uuid": titulo.uuid})
            return redirect(f"{detalhe_url}?{query_escopo}")

    return render(
        request,
        "financeiro/titulo_cancelar_confirm.html",
        {
            "titulo": titulo,
            "erro": erro,
            "escopo": escopo,
            "loja": loja,
            "query_escopo": query_escopo,
        },
    )

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
def centro_custo_editar(request, centro_uuid):
    matriz = _matriz_usuario(request)
    try:
        centro = CentroCusto.objects.get(uuid=centro_uuid, matriz=matriz)
    except CentroCusto.DoesNotExist as exc:
        raise Http404("Centro de custo nao encontrado.") from exc

    if request.method == "POST":
        form = CentroCustoForm(request.POST, instance=centro)
        if form.is_valid():
            atualizado = form.save(commit=False)
            atualizado.matriz = matriz
            atualizado.save()
            return redirect("financeiro:centros_custo")
    else:
        form = CentroCustoForm(instance=centro)

    return render(
        request,
        "financeiro/centro_custo_form.html",
        {"matriz": matriz, "form": form, "modo_edicao": True, "centro": centro},
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
def instituicao_bancaria_editar(request, instituicao_uuid):
    instituicao = get_object_or_404(InstituicaoBancaria, uuid=instituicao_uuid)

    if request.method == "POST":
        form = InstituicaoBancariaForm(request.POST, instance=instituicao)
        if form.is_valid():
            form.save()
            return redirect("financeiro:instituicoes_bancarias")
    else:
        form = InstituicaoBancariaForm(instance=instituicao)

    return render(
        request,
        "financeiro/instituicao_bancaria_form.html",
        {"form": form, "modo_edicao": True, "instituicao": instituicao},
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

@login_required
@require_permission(PERMISSAO_FINANCEIRO_GERENCIAR)
def conta_financeira_editar(request, conta_uuid):
    matriz = _matriz_usuario(request)
    conta = get_object_or_404(ContaFinanceira, uuid=conta_uuid, matriz=matriz)

    if request.method == "POST":
        form = ContaFinanceiraForm(request.POST, instance=conta)
    else:
        form = ContaFinanceiraForm(instance=conta)

    form.fields["loja"].queryset = _lojas_autorizadas(request, matriz)
    form.fields["instituicao"].queryset = InstituicaoBancaria.objects.all().order_by("nome")

    if request.method == "POST" and form.is_valid():
        atualizada = form.save(commit=False)
        atualizada.matriz = matriz
        atualizada.save()
        return redirect("financeiro:contas_financeiras")

    return render(
        request,
        "financeiro/conta_financeira_form.html",
        {"matriz": matriz, "form": form, "modo_edicao": True, "conta": conta},
    )

def _extrato_conta_contexto(request, conta_uuid):
    from django.db.models import Q
    matriz = _matriz_usuario(request)
    conta = get_object_or_404(ContaFinanceira.objects.select_related("loja", "instituicao"), uuid=conta_uuid, matriz=matriz)
    lojas = _lojas_autorizadas(request, matriz)
    if conta.loja_id is not None and not lojas.filter(pk=conta.loja_id).exists():
        raise Http404("Conta financeira fora do escopo autorizado.")
    eventos = BaixaFinanceira.objects.filter(conta_financeira=conta).select_related("forma_pagamento", "parcela__titulo", "parcela__titulo__loja")
    data_inicio=(request.GET.get("data_inicio") or "").strip(); data_fim=(request.GET.get("data_fim") or "").strip()
    tipo=(request.GET.get("tipo") or "").strip().upper(); natureza=(request.GET.get("natureza") or "").strip().upper()
    forma_pagamento=(request.GET.get("forma_pagamento") or "").strip(); busca=(request.GET.get("busca") or "").strip()
    try:
        if data_inicio: eventos=eventos.filter(data__gte=date.fromisoformat(data_inicio))
    except ValueError: data_inicio=""
    try:
        if data_fim: eventos=eventos.filter(data__lte=date.fromisoformat(data_fim))
    except ValueError: data_fim=""
    if tipo in {"BAIXA","ESTORNO"}: eventos=eventos.filter(tipo=tipo)
    else: tipo=""
    if natureza in {"PAGAR","RECEBER"}: eventos=eventos.filter(parcela__titulo__natureza=natureza)
    else: natureza=""
    if forma_pagamento: eventos=eventos.filter(forma_pagamento_id=forma_pagamento)
    if busca: eventos=eventos.filter(Q(parcela__titulo__descricao__icontains=busca)|Q(observacao__icontains=busca))
    eventos=eventos.order_by("-data","-criado_em","-pk"); lista=list(eventos)
    total_entradas=Decimal("0"); total_saidas=Decimal("0")
    for e in lista:
        entrada=(e.tipo=="ESTORNO" and e.parcela.titulo.natureza=="PAGAR") or (e.tipo=="BAIXA" and e.parcela.titulo.natureza=="RECEBER")
        if entrada: total_entradas+=e.valor
        else: total_saidas+=e.valor
    try:
        from pdv.models import FormaPagamento
        formas=FormaPagamento.objects.filter(matriz=matriz,ativa=True).order_by("nome")
    except Exception: formas=[]
    params=request.GET.copy(); params.pop("page",None)
    return {"matriz":matriz,"conta":conta,"eventos":lista,"data_inicio":data_inicio,"data_fim":data_fim,"tipo":tipo,"natureza":natureza,"forma_pagamento":forma_pagamento,"busca":busca,"formas_pagamento":formas,"total_entradas":total_entradas,"total_saidas":total_saidas,"saldo_liquido":total_entradas-total_saidas,"total_movimentacoes":len(lista),"querystring":params.urlencode()}

@login_required
@require_permission(PERMISSAO_FINANCEIRO_VISUALIZAR)
def conta_financeira_extrato(request, conta_uuid):
    contexto=_extrato_conta_contexto(request,conta_uuid)
    contexto["pagina"]=Paginator(contexto["eventos"],30).get_page(request.GET.get("page"))
    return render(request,"financeiro/conta_financeira_extrato.html",contexto)

@login_required
@require_permission(PERMISSAO_FINANCEIRO_VISUALIZAR)
def conta_financeira_extrato_pdf(request, conta_uuid):
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    contexto=_extrato_conta_contexto(request,conta_uuid); buffer=BytesIO(); styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(buffer,pagesize=landscape(A4))
    story=[Paragraph("Extrato da Conta Financeira",styles["Title"]),Paragraph(str(contexto["conta"].nome),styles["Heading2"]),Paragraph("Periodo: %s a %s"%(contexto["data_inicio"] or "inicio",contexto["data_fim"] or "fim"),styles["Normal"]),Spacer(1,12)]
    resumo=[["Entradas","Saidas","Saldo liquido","Movimentacoes"],[f'R$ {contexto["total_entradas"]:.2f}',f'R$ {contexto["total_saidas"]:.2f}',f'R$ {contexto["saldo_liquido"]:.2f}',str(contexto["total_movimentacoes"])]]
    rt=Table(resumo);rt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")]))
    story += [rt,Spacer(1,12)];dados=[["Data","Tipo","Natureza","Titulo","Forma","Loja","Valor"]]
    for e in contexto["eventos"]:
        entrada=(e.tipo=="ESTORNO" and e.parcela.titulo.natureza=="PAGAR") or (e.tipo=="BAIXA" and e.parcela.titulo.natureza=="RECEBER")
        dados.append([e.data.strftime("%d/%m/%Y"),e.get_tipo_display(),e.parcela.titulo.get_natureza_display(),e.parcela.titulo.descricao,str(e.forma_pagamento or "-"),e.parcela.titulo.loja.nome if e.parcela.titulo.loja else "Matriz",("%sR$ %.2f"%("+" if entrada else "-",e.valor))])
    tb=Table(dados,repeatRows=1);tb.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")]))
    story.append(tb);doc.build(story)
    response=HttpResponse(buffer.getvalue(),content_type="application/pdf");response["Content-Disposition"]='attachment; filename="extrato_conta_financeira.pdf"';return response


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
def baixa_estornar(request, titulo_uuid, parcela_id, baixa_id):
    from django.utils import timezone
    from financeiro.services import estornar_baixa_financeira_com_caixa

    matriz = _matriz_usuario(request)
    titulo = get_object_or_404(TituloFinanceiro, matriz=matriz, uuid=titulo_uuid)
    lojas = _lojas_autorizadas(request, matriz)
    if titulo.loja_id is None or not lojas.filter(pk=titulo.loja_id).exists():
        raise Http404("Titulo sem loja autorizada para estorno.")

    parcela = get_object_or_404(titulo.parcelas.all(), pk=parcela_id)
    baixa = get_object_or_404(
        parcela.baixas.select_related("forma_pagamento", "conta_financeira", "sessao_caixa"),
        pk=baixa_id,
        tipo=BaixaFinanceira.Tipo.BAIXA,
    )

    if request.method == "POST":
        form = EstornoBaixaForm(request.POST)
        token_idempotencia = (request.POST.get("chave_idempotencia") or "").strip()
        try:
            token_idempotencia = str(uuid.UUID(token_idempotencia))
        except (ValueError, AttributeError, TypeError):
            form.add_error(None, "Token de idempotencia invalido. Recarregue o formulario.")

        if form.is_valid() and not form.non_field_errors():
            try:
                estornar_baixa_financeira_com_caixa(
                    baixa=baixa,
                    valor=form.cleaned_data["valor"],
                    data=form.cleaned_data["data"],
                    chave_idempotencia=f"estorno-ui:{matriz.pk}:{request.user.pk}:{token_idempotencia}",
                    operador=request.user,
                    observacao=form.cleaned_data["observacao"],
                    usuario=request.user,
                    request=request,
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
        total_estornado = sum(
            (
                evento.valor
                for evento in parcela.baixas.all()
                if evento.tipo == BaixaFinanceira.Tipo.ESTORNO
                and evento.baixa_estornada_id == baixa.pk
            ),
            Decimal("0.00"),
        )
        valor_estornavel = baixa.valor - total_estornado
        form = EstornoBaixaForm(
            initial={"valor": valor_estornavel, "data": timezone.localdate()}
        )

    return render(
        request,
        "financeiro/baixa_estorno_form.html",
        {
            "titulo": titulo,
            "parcela": parcela,
            "baixa": baixa,
            "form": form,
            "chave_idempotencia": token_idempotencia,
        },
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
