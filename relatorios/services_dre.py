"""Nucleo economico da DRE gerencial do Pro-Cash.

Regime: competencia. Eventos de caixa nao sao fonte economica desta apuracao.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce

from configuracoes.models import ComissaoVendedor, FechamentoComissao
from financeiro.models import PlanoConta, TituloFinanceiro
from pdv.choices import StatusOperacaoVenda
from pdv.models import ItemVenda, Venda

REGIME_COMPETENCIA = "COMPETENCIA"
EXCLUIR_COMPRA_RECEBIMENTO_DRE = TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO
EXCLUIR_VENDA_PAGAMENTO_RECEITA = TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO
COMISSAO_SNAPSHOT = "FECHAMENTO_COMISSAO"
DEVOLUCAO_VENDA_NAO_IMPLEMENTADA = True

# CONTRATO_SINAL_DRE: valores economicos manuais sao positivos.
# REVERSAO_DRE_EXPLICITA exige fato economico proprio futuro; nao usamos abs().
CONTRATO_SINAL_DRE = "VALOR_ECONOMICO_POSITIVO"
REVERSAO_DRE_EXPLICITA = True

# ESCOPO_CENTRO_CUSTO_DRE: filtro analitico APENAS_LANCAMENTOS_CLASSIFICADOS.
# CENTRO_CUSTO_NAO_FILTRA_VENDAS_CMV_COMISSOES enquanto essas origens nao tiverem atribuicao.
ESCOPO_CENTRO_CUSTO_DRE = "APENAS_LANCAMENTOS_CLASSIFICADOS"
CENTRO_CUSTO_NAO_FILTRA_VENDAS_CMV_COMISSOES = True

# COMPETENCIA_COMISSAO_MES_FECHADO: snapshot mensal e indivisivel.
# PERIODO_PARCIAL_EXCLUI_COMISSAO_MENSAL se o mes nao estiver inteiro no intervalo.
COMPETENCIA_COMISSAO_MES_FECHADO = True
PERIODO_PARCIAL_EXCLUI_COMISSAO_MENSAL = True

ZERO = Decimal("0.00")
MONEY = DecimalField(max_digits=18, decimal_places=2)


@dataclass(frozen=True)
class ResultadoDRE:
    receita_bruta: Decimal
    acrescimos: Decimal
    deducoes_receita: Decimal
    receita_liquida: Decimal
    cmv: Decimal
    lucro_bruto: Decimal
    despesas_operacionais: Decimal
    resultado_operacional: Decimal
    resultado_financeiro: Decimal
    outras_receitas_despesas: Decimal
    resultado_antes_impostos: Decimal
    margem_bruta: Decimal
    margem_operacional: Decimal
    memoria_calculo: dict


def _periodo(qs, campo, inicio, fim):
    return qs.filter(**{f"{campo}__date__gte": inicio, f"{campo}__date__lte": fim})


def _soma(qs, campo):
    return qs.aggregate(v=Coalesce(Sum(campo), ZERO, output_field=MONEY))["v"]


def _vendas_validas(*, matriz, inicio, fim, loja=None):
    qs = Venda.objects.filter(
        matriz=matriz,
        status=StatusOperacaoVenda.FINALIZADA,
        finalizada_em__date__gte=inicio,
        finalizada_em__date__lte=fim,
        cancelada_em__isnull=True,
    )
    if loja is not None:
        qs = qs.filter(loja=loja)
    return qs


def _valor_titulo(titulo):
    bruto = titulo.valor_bruto if titulo.valor_bruto is not None else titulo.valor_original
    return Decimal(bruto) - Decimal(titulo.valor_desconto) + Decimal(titulo.valor_juros)


def calcular_dre(*, matriz, inicio: date, fim: date, loja=None, centro_custo=None):
    """Calcula a DRE gerencial por competencia para o periodo informado."""
    vendas = _vendas_validas(matriz=matriz, inicio=inicio, fim=fim, loja=loja)

    # Contrato economico da venda:
    # receita_bruta = subtotal + acrescimos; deducoes_receita = descontos.
    subtotal = _soma(vendas, "subtotal")
    acrescimos = _soma(vendas, "acrescimo")
    descontos_venda = _soma(vendas, "desconto")
    receita_bruta = subtotal + acrescimos

    itens = ItemVenda.objects.filter(venda__in=vendas, cancelado=False)
    custo_expr = ExpressionWrapper(
        F("quantidade") * F("custo_unitario_snapshot"),
        output_field=MONEY,
    )
    cmv = itens.aggregate(
        v=Coalesce(Sum(custo_expr), ZERO, output_field=MONEY)
    )["v"]

    # Titulos de venda representam contas a receber, nao receita operacional.
    # Recebimentos de compra representam estoque/obrigacao, nao CMV/despesa automatica.
    titulos = TituloFinanceiro.objects.filter(
        matriz=matriz,
        data_competencia__gte=inicio,
        data_competencia__lte=fim,
        plano_conta__classificacao_dre__isnull=False,
    ).exclude(
        status=TituloFinanceiro.Status.CANCELADO
    ).exclude(
        origem_tipo__in=[
            EXCLUIR_COMPRA_RECEBIMENTO_DRE,
            EXCLUIR_VENDA_PAGAMENTO_RECEITA,
            TituloFinanceiro.OrigemTipo.COMISSAO,
        ]
    ).select_related("plano_conta")

    if loja is not None:
        titulos = titulos.filter(loja=loja)
    if centro_custo is not None:
        titulos = titulos.filter(centro_custo=centro_custo)

    deducoes_financeiras = ZERO
    despesas_operacionais = ZERO
    resultado_financeiro = ZERO
    outras_receitas_despesas = ZERO

    for titulo in titulos:
        valor = _valor_titulo(titulo)
        classificacao_dre = titulo.plano_conta.classificacao_dre
        sinal = Decimal("-1.00") if titulo.natureza == TituloFinanceiro.Natureza.PAGAR else Decimal("1.00")

        if classificacao_dre == PlanoConta.ClassificacaoDRE.DEDUCAO_RECEITA:
            # Deducao reduz receita independentemente de ser armazenada como pagar/receber.
            deducoes_financeiras += valor
        elif classificacao_dre == PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL:
            despesas_operacionais += valor
        elif classificacao_dre == PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO:
            resultado_financeiro += valor * sinal
        elif classificacao_dre == PlanoConta.ClassificacaoDRE.OUTRA_RECEITA_DESPESA:
            outras_receitas_despesas += valor * sinal

    # Comissao e despesa economica na competencia do fechamento, independentemente
    # de quando/mesmo se o titulo financeiro posterior for criado ou pago.
    fechamentos = FechamentoComissao.objects.filter(
        matriz=matriz,
    )
    if loja is not None:
        fechamentos = fechamentos.filter(loja=loja)

    competencia_q = Q()
    atual = date(inicio.year, inicio.month, 1)
    limite = date(fim.year, fim.month, 1)
    while atual <= limite:
        proximo = date(atual.year + (1 if atual.month == 12 else 0), 1 if atual.month == 12 else atual.month + 1, 1)
        ultimo_dia = (proximo - timedelta(days=1)).day
        mes_inteiro_no_periodo = (((atual.year, atual.month) > (inicio.year, inicio.month) or inicio.day == 1) and ((atual.year, atual.month) < (fim.year, fim.month) or fim.day == ultimo_dia))
        if mes_inteiro_no_periodo:
            competencia_q |= Q(competencia_ano=atual.year, competencia_mes=atual.month)
        atual = proximo

    if competencia_q.children:
        fechamentos_competencia = fechamentos.filter(competencia_q)
    else:
        fechamentos_competencia = fechamentos.none()

    comissoes = ComissaoVendedor.objects.filter(
        fechamento__in=fechamentos_competencia,
        elegivel=True,
        valor_comissao__gt=ZERO,
    )
    despesas_operacionais += _soma(comissoes, "valor_comissao")

    deducoes_receita = descontos_venda + deducoes_financeiras
    receita_liquida = receita_bruta - deducoes_receita
    lucro_bruto = receita_liquida - cmv
    resultado_operacional = lucro_bruto - despesas_operacionais
    resultado_antes_impostos = (
        resultado_operacional + resultado_financeiro + outras_receitas_despesas
    )

    margem_bruta = (
        (lucro_bruto / receita_liquida) * Decimal("100.00")
        if receita_liquida != ZERO else ZERO
    )
    margem_operacional = (
        (resultado_operacional / receita_liquida) * Decimal("100.00")
        if receita_liquida != ZERO else ZERO
    )

    # Memoria reconciliavel: IDs das operacoes efetivamente consideradas.
    origens_receita = list(vendas.values_list("pk", flat=True))
    origens_cmv = list(itens.values_list("pk", flat=True))
    origens_despesas = {"titulos": list(titulos.values_list("pk", flat=True)), "comissoes": list(comissoes.values_list("pk", flat=True))}
    titulos_por_linha = {"deducoes_receita": [], "despesas_operacionais": [], "resultado_financeiro": [], "outras_receitas_despesas": []}
    mapa_classificacao_linha = {
        PlanoConta.ClassificacaoDRE.DEDUCAO_RECEITA: "deducoes_receita",
        PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL: "despesas_operacionais",
        PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO: "resultado_financeiro",
        PlanoConta.ClassificacaoDRE.OUTRA_RECEITA_DESPESA: "outras_receitas_despesas",
    }
    for titulo in titulos:
        linha = mapa_classificacao_linha.get(titulo.plano_conta.classificacao_dre)
        if linha:
            titulos_por_linha[linha].append(titulo.pk)
    memoria_calculo = {
        "origens_receita": origens_receita, "origens_cmv": origens_cmv, "origens_despesas": origens_despesas,
        "origens_por_linha": {
            "deducoes_receita": {"titulos": titulos_por_linha["deducoes_receita"]},
            "despesas_operacionais": {"titulos": titulos_por_linha["despesas_operacionais"], "comissoes": list(comissoes.values_list("pk", flat=True))},
            "resultado_financeiro": {"titulos": titulos_por_linha["resultado_financeiro"]},
            "outras_receitas_despesas": {"titulos": titulos_por_linha["outras_receitas_despesas"]},
        },
    }

    return ResultadoDRE(
        receita_bruta=receita_bruta,
        acrescimos=acrescimos,
        deducoes_receita=deducoes_receita,
        receita_liquida=receita_liquida,
        cmv=cmv,
        lucro_bruto=lucro_bruto,
        despesas_operacionais=despesas_operacionais,
        resultado_operacional=resultado_operacional,
        resultado_financeiro=resultado_financeiro,
        outras_receitas_despesas=outras_receitas_despesas,
        resultado_antes_impostos=resultado_antes_impostos,
        margem_bruta=margem_bruta,
        margem_operacional=margem_operacional,
        memoria_calculo=memoria_calculo,
    )
@dataclass(frozen=True)
class ComparativoDRE:
    atual: ResultadoDRE
    anterior: ResultadoDRE
    variacao_absoluta: dict
    variacao_percentual: dict

CAMPOS_GERENCIAIS_DRE = (
    "receita_bruta", "deducoes_receita", "receita_liquida", "cmv", "lucro_bruto",
    "despesas_operacionais", "resultado_operacional", "resultado_financeiro",
    "outras_receitas_despesas", "resultado_antes_impostos",
)

def calcular_analise_vertical(resultado):
    """Percentuais das linhas sobre a receita liquida."""
    base = resultado.receita_liquida
    return {campo: ((getattr(resultado, campo) / base) * Decimal("100.00") if base != ZERO else ZERO) for campo in CAMPOS_GERENCIAIS_DRE}

def _variacao_percentual(atual, anterior):
    if anterior == ZERO:
        return ZERO if atual == ZERO else None
    return ((atual - anterior) / abs(anterior)) * Decimal("100.00")

def comparar_periodos(*, matriz, inicio, fim, inicio_anterior, fim_anterior, loja=None, centro_custo=None):
    atual = calcular_dre(matriz=matriz, inicio=inicio, fim=fim, loja=loja, centro_custo=centro_custo)
    anterior = calcular_dre(matriz=matriz, inicio=inicio_anterior, fim=fim_anterior, loja=loja, centro_custo=centro_custo)
    absoluta = {}; percentual = {}
    for campo in CAMPOS_GERENCIAIS_DRE:
        va=getattr(atual,campo); vp=getattr(anterior,campo)
        absoluta[campo]=va-vp; percentual[campo]=_variacao_percentual(va,vp)
    return ComparativoDRE(atual=atual, anterior=anterior, variacao_absoluta=absoluta, variacao_percentual=percentual)

def apurar_evolucao_mensal(*, matriz, inicio, fim, loja=None, centro_custo=None):
    pontos=[]; atual=date(inicio.year,inicio.month,1); limite=date(fim.year,fim.month,1)
    while atual <= limite:
        proximo=date(atual.year+(1 if atual.month==12 else 0),1 if atual.month==12 else atual.month+1,1)
        ultimo=proximo-timedelta(days=1)
        ini=max(inicio,atual); fim_mes=min(fim,ultimo)
        resultado=calcular_dre(matriz=matriz,inicio=ini,fim=fim_mes,loja=loja,centro_custo=centro_custo)
        pontos.append({"ano":atual.year,"mes":atual.month,"inicio":ini,"fim":fim_mes,"resultado":resultado})
        atual=proximo
    return pontos

def obter_drilldown_dre(resultado, linha):
    memoria = resultado.memoria_calculo
    por_linha = memoria.get("origens_por_linha", {})
    if linha == "receita_bruta": return {"vendas": list(memoria.get("origens_receita", []))}
    if linha == "deducoes_receita":
        dados = por_linha.get(linha, {})
        return {"vendas": list(memoria.get("origens_receita", [])), "titulos": list(dados.get("titulos", []))}
    if linha == "cmv": return {"itens_venda": list(memoria.get("origens_cmv", []))}
    if linha in ("despesas_operacionais", "resultado_financeiro", "outras_receitas_despesas"):
        dados = por_linha.get(linha, {})
        retorno = {"titulos": list(dados.get("titulos", []))}
        if linha == "despesas_operacionais": retorno["comissoes"] = list(dados.get("comissoes", []))
        return retorno
    derivados = {
        "receita_liquida": {"tipo": "DERIVADO", "formula": "receita_bruta - deducoes_receita", "componentes": ["receita_bruta", "deducoes_receita"]},
        "lucro_bruto": {"tipo": "DERIVADO", "formula": "receita_liquida - cmv", "componentes": ["receita_liquida", "cmv"]},
        "resultado_operacional": {"tipo": "DERIVADO", "formula": "lucro_bruto - despesas_operacionais", "componentes": ["lucro_bruto", "despesas_operacionais"]},
        "resultado_antes_impostos": {"tipo": "DERIVADO", "formula": "resultado_operacional + resultado_financeiro + outras_receitas_despesas", "componentes": ["resultado_operacional", "resultado_financeiro", "outras_receitas_despesas"]},
    }
    return derivados.get(linha, {})

def apurar_dre(*, matriz, inicio, fim, loja=None, centro_custo=None, periodo_anterior=None):
    resultado=calcular_dre(matriz=matriz,inicio=inicio,fim=fim,loja=loja,centro_custo=centro_custo)
    dados={"resultado":resultado,"analise_vertical":calcular_analise_vertical(resultado),"drilldown":{linha:obter_drilldown_dre(resultado,linha) for linha in CAMPOS_GERENCIAIS_DRE}}
    if periodo_anterior is not None:
        ia,fa=periodo_anterior
        dados["comparativo"]=comparar_periodos(matriz=matriz,inicio=inicio,fim=fim,inicio_anterior=ia,fim_anterior=fa,loja=loja,centro_custo=centro_custo)
    return dados
