from django import template

register = template.Library()


@register.filter
def moeda_br(valor):
    if valor is None:
        valor = 0

    valor = float(valor)

    return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')