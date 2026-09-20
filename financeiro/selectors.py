from decimal import Decimal

from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro


ESCOPO_CONSOLIDADO = "consolidado"
ESCOPO_MATRIZ = "matriz"
ESCOPO_LOJA = "loja"
ESCOPOS_VALIDOS = {ESCOPO_CONSOLIDADO, ESCOPO_MATRIZ, ESCOPO_LOJA}


def _validar_escopo(*, matriz, escopo, loja):
    if escopo not in ESCOPOS_VALIDOS:
        raise ValueError("Escopo financeiro invalido.")

    if escopo == ESCOPO_LOJA and loja is None:
        raise ValueError("O escopo de loja exige uma loja.")

    if loja is not None and loja.matriz_id != matriz.id:
        return False

    return True


def _aplicar_escopo_titulo(queryset, *, matriz, escopo, loja):
    escopo_valido = _validar_escopo(
        matriz=matriz,
        escopo=escopo,
        loja=loja,
    )
    if not escopo_valido:
        return queryset.none()
    if escopo == ESCOPO_MATRIZ:
        return queryset.filter(loja__isnull=True)
    if escopo == ESCOPO_LOJA:
        return queryset.filter(loja=loja)
    if loja is not None:
        return queryset.filter(loja=loja)
    return queryset


def listar_titulos(*, matriz, natureza=None, status=None, escopo=ESCOPO_CONSOLIDADO, loja=None):
    queryset = TituloFinanceiro.objects.filter(matriz=matriz).select_related("loja")
    queryset = _aplicar_escopo_titulo(queryset, matriz=matriz, escopo=escopo, loja=loja)
    if natureza is not None:
        queryset = queryset.filter(natureza=natureza)
    if status is not None:
        queryset = queryset.filter(status=status)
    return queryset.order_by("-data_emissao", "-id")


def parcelas_em_aberto(*, matriz, natureza=None, escopo=ESCOPO_CONSOLIDADO, loja=None):
    queryset = ParcelaFinanceira.objects.filter(
        titulo__matriz=matriz,
        status__in=[ParcelaFinanceira.Status.ABERTO, ParcelaFinanceira.Status.PARCIAL],
    ).select_related("titulo", "titulo__loja")
    escopo_valido = _validar_escopo(
        matriz=matriz,
        escopo=escopo,
        loja=loja,
    )
    if not escopo_valido:
        return queryset.none()
    if escopo == ESCOPO_MATRIZ:
        queryset = queryset.filter(titulo__loja__isnull=True)
    elif escopo == ESCOPO_LOJA:
        queryset = queryset.filter(titulo__loja=loja)
    elif loja is not None:
        queryset = queryset.filter(titulo__loja=loja)
    if natureza is not None:
        queryset = queryset.filter(titulo__natureza=natureza)
    return queryset.order_by("vencimento", "titulo_id", "numero")


def resumo_saldos(*, matriz, escopo=ESCOPO_CONSOLIDADO, loja=None):
    titulos = TituloFinanceiro.objects.filter(matriz=matriz).exclude(status=TituloFinanceiro.Status.CANCELADO)
    titulos = _aplicar_escopo_titulo(titulos, matriz=matriz, escopo=escopo, loja=loja)
    resultado = {
        TituloFinanceiro.Natureza.RECEBER: Decimal("0.00"),
        TituloFinanceiro.Natureza.PAGAR: Decimal("0.00"),
    }
    parcelas = ParcelaFinanceira.objects.filter(titulo__in=titulos).select_related("titulo").prefetch_related("baixas")
    for parcela in parcelas:
        total_baixas = sum((e.valor for e in parcela.baixas.all() if e.tipo == BaixaFinanceira.Tipo.BAIXA), Decimal("0.00"))
        total_estornos = sum((e.valor for e in parcela.baixas.all() if e.tipo == BaixaFinanceira.Tipo.ESTORNO), Decimal("0.00"))
        saldo = parcela.valor_original - total_baixas + total_estornos
        resultado[parcela.titulo.natureza] += saldo
    return {
        "receber": resultado[TituloFinanceiro.Natureza.RECEBER],
        "pagar": resultado[TituloFinanceiro.Natureza.PAGAR],
    }
