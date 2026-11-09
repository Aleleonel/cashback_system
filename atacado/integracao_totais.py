"""F32P3E: conciliacao exata de valores antes da consolidacao.

Esta funcao e pura: nao cria vendas, nao confirma reservas e nao movimenta caixa.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.core.exceptions import ValidationError

CENTAVO = Decimal("0.01")


def dinheiro(valor, campo):
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({campo: "Valor monetario invalido."})
    if not numero.is_finite():
        raise ValidationError({campo: "Valor monetario nao finito."})
    if numero != numero.quantize(CENTAVO, rounding=ROUND_HALF_UP):
        raise ValidationError({campo: "Valor com mais de duas casas decimais."})
    return numero


def conciliar_total_pedido(*, subtotal_itens, desconto, acrescimo, total_pedido):
    """Exige igualdade exata entre itens/ajustes e total do pedido.

    A alocacao de frete e ajustes negociados nos campos PDV e etapa posterior.
    """
    subtotal = dinheiro(subtotal_itens, "subtotal_itens")
    desc = dinheiro(desconto, "desconto")
    acres = dinheiro(acrescimo, "acrescimo")
    esperado = dinheiro(total_pedido, "total_pedido")
    if min(subtotal, desc, acres, esperado) < 0:
        raise ValidationError("Valores monetarios nao podem ser negativos.")
    calculado = subtotal - desc + acres
    if calculado != esperado:
        raise ValidationError({"total_pedido": f"Divergencia: calculado={calculado}; pedido={esperado}."})
    return esperado
