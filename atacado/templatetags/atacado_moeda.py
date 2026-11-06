"""Formato monetario brasileiro apenas para apresentacao."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django import template

register = template.Library()

@register.filter(name="moeda_br")
def moeda_br(valor):
    if valor is None or valor == "":
        return "0,00"
    try:
        quantia = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return "0,00"
    return format(quantia, ",.2f").replace(",", "_").replace(".", ",").replace("_", ".")
