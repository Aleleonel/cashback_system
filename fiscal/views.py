from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.services import usuario_tem_permissao
from core.services import get_contexto_operacional_usuario
from fiscal.constants import (
    PERMISSAO_FISCAL_CONFIGURAR,
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
)
from fiscal.forms import OrigemMercadoriaForm
from fiscal.models import (
    BeneficioFiscal,
    CEST,
    CFOP,
    CSOSN,
    CSTCOFINS,
    CSTICMS,
    CSTIPI,
    CSTPIS,
    NCM,
    OrigemMercadoria,
    RegraFiscal,
)
from fiscal.selectors import (
    get_origem_mercadoria,
    get_origens_mercadoria,
)
from fiscal.services import (
    criar_origem_mercadoria,
    editar_origem_mercadoria,
)


def _aplicar_erros_no_form(*, form, erro):
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


def _obter_origem_ou_404(*, origem_id):
    try:
        return get_origem_mercadoria(
            origem_id=origem_id,
        )
    except ObjectDoesNotExist as erro:
        raise Http404(
            "Origem da mercadoria nao encontrada."
        ) from erro


@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def inicio(request):
    contexto = get_contexto_operacional_usuario(request.user)
    pode_gerenciar = usuario_tem_permissao(
        request.user,
        PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    )

    pode_configurar = usuario_tem_permissao(
        request.user,
        PERMISSAO_FISCAL_CONFIGURAR,
    )

    def resumo(model):
        total = model.objects.count()
        ativos = model.objects.filter(ativo=True).count()
        return {"total": total, "ativos": ativos, "inativos": total - ativos}

    referencias = (
        {"codigo": "origens", "titulo": "Origens da mercadoria", "descricao": "Codigos oficiais de origem usados na tributacao dos produtos.", "icone": "bi-globe-americas", "url_name": "fiscal:lista_origens_mercadoria", "resumo": resumo(OrigemMercadoria)},
        {"codigo": "cst_icms", "titulo": "CST ICMS", "descricao": "Situacoes tributarias do ICMS para empresas do regime normal.", "icone": "bi-percent", "url_name": "fiscal:lista_csts_icms", "resumo": resumo(CSTICMS)},
        {"codigo": "csosn", "titulo": "CSOSN", "descricao": "Situacoes tributarias aplicaveis ao Simples Nacional.", "icone": "bi-diagram-3", "url_name": "fiscal:lista_csosns", "resumo": resumo(CSOSN)},
        {"codigo": "cfop", "titulo": "CFOP", "descricao": "Codigos fiscais de entradas, saidas, devolucoes e remessas.", "icone": "bi-arrow-left-right", "url_name": "fiscal:lista_cfops", "resumo": resumo(CFOP)},
        {"codigo": "ncm", "titulo": "NCM", "descricao": "Classificacao fiscal oficial das mercadorias.", "icone": "bi-list-ol", "url_name": "fiscal:lista_ncms", "resumo": resumo(NCM)},
        {"codigo": "cst_pis", "titulo": "CST PIS", "descricao": "Situacoes tributarias do PIS para entradas e saidas.", "icone": "bi-p-circle", "url_name": "fiscal:lista_csts_pis", "resumo": resumo(CSTPIS)},
        {"codigo": "cst_cofins", "titulo": "CST COFINS", "descricao": "Situacoes tributarias da COFINS para entradas e saidas.", "icone": "bi-c-circle", "url_name": "fiscal:lista_csts_cofins", "resumo": resumo(CSTCOFINS)},
        {"codigo": "cst_ipi", "titulo": "CST IPI", "descricao": "Situacoes tributarias do IPI para operacoes com produtos.", "icone": "bi-building", "url_name": "fiscal:lista_csts_ipi", "resumo": resumo(CSTIPI)},
        {"codigo": "cest", "titulo": "CEST", "descricao": "Classificacao de mercadorias sujeitas a substituicao tributaria.", "icone": "bi-tags", "url_name": "fiscal:lista_cests", "resumo": resumo(CEST)},
    )

    inteligencia = (
        {"codigo": "beneficios", "titulo": "Beneficios fiscais", "descricao": "Desoneracoes, reducoes, creditos e fundamentos legais.", "icone": "bi-award", "url_name": "fiscal:lista_beneficios_fiscais", "resumo": resumo(BeneficioFiscal)},
        {"codigo": "regras", "titulo": "Regras fiscais", "descricao": "Condicoes e parametros utilizados pelo Motor de Selecao Fiscal.", "icone": "bi-diagram-3-fill", "url_name": "fiscal:lista_regras_fiscais", "resumo": resumo(RegraFiscal)},
    )

    proximas_etapas = (
        {"titulo": "Simulador fiscal", "descricao": "Selecao de regra e memoria de calculo em ambiente de homologacao.", "icone": "bi-calculator", "status": "Proxima aplicacao"},
        {"titulo": "Produtos fiscais", "descricao": "Vinculacao de NCM, CEST e origem ao cadastro de produtos.", "icone": "bi-box-seam", "status": "Planejado"},
        {"titulo": "Emissao fiscal", "descricao": "Preparacao de NFC-e, NF-e, contingencia e documentos auxiliares.", "icone": "bi-receipt-cutoff", "status": "Planejado"},
    )

    todos = (*referencias, *inteligencia)
    indicadores = (
        {"titulo": "Cadastros disponiveis", "valor": len(todos), "icone": "bi-collection", "descricao": "Referencias e inteligencia", "tom": "primary"},
        {"titulo": "Registros fiscais", "valor": sum(x["resumo"]["total"] for x in todos), "icone": "bi-database", "descricao": "Total cadastrado", "tom": "dark"},
        {"titulo": "Registros ativos", "valor": sum(x["resumo"]["ativos"] for x in todos), "icone": "bi-check-circle", "descricao": "Disponiveis para uso", "tom": "success"},
        {"titulo": "Regras ativas", "valor": inteligencia[1]["resumo"]["ativos"], "icone": "bi-diagram-3", "descricao": "Motor de selecao", "tom": "info"},
    )

    return render(
        request,
        "fiscal/inicio.html",
        {
            "matriz": contexto["matriz"],
            "loja": contexto.get("loja"),
            "pode_gerenciar": pode_gerenciar,
            "pode_configurar": pode_configurar,
            "indicadores": indicadores,
            "modulos_referencia": referencias,
            "modulos_inteligencia": inteligencia,
            "proximas_etapas": proximas_etapas,
            "modulos": todos,
        },
    )

@login_required
@require_permission(PERMISSAO_FISCAL_VISUALIZAR)
def lista_origens_mercadoria(request):
    busca = request.GET.get("busca", "").strip()
    somente_ativas = request.GET.get("ativas") == "1"

    origens = get_origens_mercadoria(
        busca=busca,
        somente_ativas=somente_ativas,
    )

    pagina = Paginator(origens, 25).get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "fiscal/origens_mercadoria/lista.html",
        {
            "pagina": pagina,
            "busca": busca,
            "somente_ativas": somente_ativas,
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def criar_origem_mercadoria_view(request):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)

    if request.method == "POST":
        form = OrigemMercadoriaForm(request.POST)

        if form.is_valid():
            try:
                criar_origem_mercadoria(
                    dados=form.cleaned_data,
                    usuario_executor=request.user,
                    matriz=matriz,
                    loja=loja,
                    request=request,
                )
            except ValidationError as erro:
                _aplicar_erros_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(
                    request,
                    "Origem da mercadoria criada com sucesso.",
                )
                return redirect(
                    "fiscal:lista_origens_mercadoria"
                )
    else:
        form = OrigemMercadoriaForm()

    return render(
        request,
        "fiscal/origens_mercadoria/form.html",
        {
            "form": form,
            "titulo": "Nova origem da mercadoria",
        },
    )


@login_required
@require_permission(PERMISSAO_FISCAL_GERENCIAR_CADASTROS)
def editar_origem_mercadoria_view(request, origem_id):
    matriz = getattr(request.user, "matriz", None)
    loja = getattr(request.user, "loja", None)
    origem = _obter_origem_ou_404(
        origem_id=origem_id,
    )

    if request.method == "POST":
        form = OrigemMercadoriaForm(
            request.POST,
            instance=origem,
        )

        if form.is_valid():
            try:
                editar_origem_mercadoria(
                    origem=origem,
                    dados=form.cleaned_data,
                    usuario_executor=request.user,
                    matriz=matriz,
                    loja=loja,
                    request=request,
                )
            except ValidationError as erro:
                _aplicar_erros_no_form(
                    form=form,
                    erro=erro,
                )
            else:
                messages.success(
                    request,
                    "Origem da mercadoria atualizada com sucesso.",
                )
                return redirect(
                    "fiscal:lista_origens_mercadoria"
                )
    else:
        form = OrigemMercadoriaForm(
            instance=origem,
        )

    return render(
        request,
        "fiscal/origens_mercadoria/form.html",
        {
            "form": form,
            "titulo": "Editar origem da mercadoria",
            "origem": origem,
        },
    )
