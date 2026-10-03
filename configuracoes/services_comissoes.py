from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Hashable, Mapping, Sequence


CENTAVOS = Decimal("0.01")
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ResultadoComissoes:
    percentual_aplicado: Decimal
    comissoes: dict[Hashable, Decimal]


def _dinheiro(valor: Decimal) -> Decimal:
    return Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def calcular_comissoes_por_metas(
    *,
    total_loja: Decimal,
    vendas_por_vendedor: Mapping[Hashable, Decimal],
    metas: Sequence[Mapping[str, Decimal]],
    exigir_minimo_individual: bool,
    minimo_individual: Decimal,
) -> ResultadoComissoes:
    total_loja = Decimal(total_loja)
    minimo_individual = Decimal(minimo_individual)

    atingidas = [
        meta
        for meta in metas
        if total_loja >= Decimal(meta["valor_meta"])
    ]
    percentual = (
        max(
            atingidas,
            key=lambda meta: Decimal(meta["valor_meta"]),
        )["percentual"]
        if atingidas
        else ZERO
    )
    percentual = Decimal(percentual)

    comissoes = {}
    for vendedor, total_vendedor in vendas_por_vendedor.items():
        total_vendedor = Decimal(total_vendedor)
        elegivel = (
            not exigir_minimo_individual
            or total_vendedor >= minimo_individual
        )
        valor = (
            total_vendedor * percentual / Decimal("100")
            if elegivel and percentual > ZERO
            else ZERO
        )
        comissoes[vendedor] = _dinheiro(valor)

    return ResultadoComissoes(
        percentual_aplicado=percentual,
        comissoes=comissoes,
    )

def selecionar_vendas_validas_competencia(queryset, *, loja_id: int, ano: int, mes: int):
    from pdv.models import StatusOperacaoVenda
    """Seleciona vendas finalizadas, nÃ£o canceladas, de uma loja e competÃªncia mensal."""
    from datetime import datetime
    from django.utils import timezone

    inicio = timezone.make_aware(datetime(ano, mes, 1))
    if mes == 12:
        proximo_mes = timezone.make_aware(datetime(ano + 1, 1, 1))
    else:
        proximo_mes = timezone.make_aware(datetime(ano, mes + 1, 1))

    return queryset.filter(
        loja_id=loja_id,
        status=StatusOperacaoVenda.FINALIZADA,
        finalizada_em__gte=inicio,
        finalizada_em__lt=proximo_mes,
        cancelada_em__isnull=True,
    )

@dataclass(frozen=True)
class ResultadoOrquestracaoComissoes:
    total_loja: Decimal
    percentual_aplicado: Decimal
    vendas_por_vendedor: dict
    comissoes: dict


def orquestrar_comissoes_competencia(
    *,
    vendas_validas,
    metas,
    exigir_minimo_individual: bool,
    minimo_individual: Decimal,
):
    vendas_por_vendedor = {}
    total_loja = Decimal("0.00")

    for venda in vendas_validas:
        valor = Decimal(venda.total)
        total_loja += valor
        vendas_por_vendedor[venda.vendedor_id] = (
            vendas_por_vendedor.get(venda.vendedor_id, Decimal("0.00")) + valor
        )

    calculo = calcular_comissoes_por_metas(
        total_loja=total_loja,
        vendas_por_vendedor=vendas_por_vendedor,
        metas=metas,
        exigir_minimo_individual=exigir_minimo_individual,
        minimo_individual=minimo_individual,
    )

    return ResultadoOrquestracaoComissoes(
        total_loja=total_loja.quantize(Decimal("0.01")),
        percentual_aplicado=calculo.percentual_aplicado,
        vendas_por_vendedor={
            vendedor_id: valor.quantize(Decimal("0.01"))
            for vendedor_id, valor in vendas_por_vendedor.items()
        },
        comissoes=calculo.comissoes,
    )