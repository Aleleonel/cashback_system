from django import template

register = template.Library()


@register.filter
def moeda_br(valor):
    if valor is None:
        valor = 0

    valor = float(valor)

    return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
# BEGIN PDV-02 FORMATADORES DEFINITIVOS
@register.filter(name="quantidade_br")
def quantidade_br(valor):
    from decimal import Decimal, InvalidOperation

    if valor is None or valor == "":
        numero = Decimal("0")
    else:
        try:
            numero = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError):
            return valor

    numero = numero.quantize(Decimal("0.001"))

    if numero == numero.to_integral():
        texto = f"{numero:,.0f}"
    else:
        texto = f"{numero:,.3f}".rstrip("0").rstrip(".")

    return texto.replace(",", "#").replace(".", ",").replace("#", ".")
# END PDV-02 FORMATADORES DEFINITIVOS
