from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from .models import FaixaAtacado

CENTAVOS = Decimal("0.01")


def obter_faixa_atacado(config, valor_base):
    valor_base = Decimal(valor_base)
    return (
        FaixaAtacado.objects.filter(
            configuracao=config,
            valor_minimo__lte=valor_base,
        )
        .filter(Q(valor_maximo__isnull=True) | Q(valor_maximo__gte=valor_base))
        .order_by("-valor_minimo", "id")
        .first()
    )


def calcular_base_enquadramento_atacado(
    *,
    config,
    valor_itens_elegiveis,
    valor_itens_promocionais=Decimal("0.00"),
):
    elegiveis = Decimal(valor_itens_elegiveis)
    promocionais = Decimal(valor_itens_promocionais)
    if config.produto_promocional_conta_para_faixa_atacado:
        return elegiveis + promocionais
    return elegiveis


def calcular_desconto_atacado(*, valor_elegivel, percentual):
    valor = Decimal(valor_elegivel)
    taxa = Decimal(percentual) / Decimal("100")
    return (valor * taxa).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
