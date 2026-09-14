from decimal import Decimal

from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro


def listar_titulos(*, matriz, natureza=None, status=None, loja=None):
    queryset = TituloFinanceiro.objects.filter(matriz=matriz).select_related("loja")

    if natureza is not None:
        queryset = queryset.filter(natureza=natureza)
    if status is not None:
        queryset = queryset.filter(status=status)
    if loja is not None:
        queryset = queryset.filter(loja=loja)

    return queryset.order_by("-data_emissao", "-id")


def parcelas_em_aberto(*, matriz, natureza=None, loja=None):
    queryset = (
        ParcelaFinanceira.objects.filter(
            titulo__matriz=matriz,
            status__in=[
                ParcelaFinanceira.Status.ABERTO,
                ParcelaFinanceira.Status.PARCIAL,
            ],
        )
        .select_related("titulo", "titulo__loja")
    )

    if natureza is not None:
        queryset = queryset.filter(titulo__natureza=natureza)
    if loja is not None:
        queryset = queryset.filter(titulo__loja=loja)

    return queryset.order_by("vencimento", "titulo_id", "numero")


def resumo_saldos(*, matriz, loja=None):
    titulos = TituloFinanceiro.objects.filter(matriz=matriz).exclude(
        status=TituloFinanceiro.Status.CANCELADO
    )
    if loja is not None:
        titulos = titulos.filter(loja=loja)

    resultado = {
        TituloFinanceiro.Natureza.RECEBER: Decimal("0.00"),
        TituloFinanceiro.Natureza.PAGAR: Decimal("0.00"),
    }

    parcelas = (
        ParcelaFinanceira.objects.filter(titulo__in=titulos)
        .select_related("titulo")
        .prefetch_related("baixas")
    )
    for parcela in parcelas:
        total_baixas = sum(
            (
                evento.valor
                for evento in parcela.baixas.all()
                if evento.tipo == BaixaFinanceira.Tipo.BAIXA
            ),
            Decimal("0.00"),
        )
        total_estornos = sum(
            (
                evento.valor
                for evento in parcela.baixas.all()
                if evento.tipo == BaixaFinanceira.Tipo.ESTORNO
            ),
            Decimal("0.00"),
        )
        saldo = parcela.valor_original - total_baixas + total_estornos
        resultado[parcela.titulo.natureza] += saldo

    return {
        "receber": resultado[TituloFinanceiro.Natureza.RECEBER],
        "pagar": resultado[TituloFinanceiro.Natureza.PAGAR],
    }