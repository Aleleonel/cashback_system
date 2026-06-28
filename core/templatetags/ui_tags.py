from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.simple_tag
def auditoria_badge_class(acao):

    classes = {
        'login': 'bg-success',
        'logout': 'bg-secondary',
        'criar': 'bg-primary',
        'editar': 'bg-warning text-dark',
        'excluir': 'bg-danger',
        'importar': 'bg-info text-dark',
        'disparar': 'bg-dark',
        'acessar': 'bg-secondary',
    }

    return classes.get(
        acao,
        'bg-secondary'
    )


@register.simple_tag
def auditoria_icone(acao):

    icones = {
        'login': 'bi-box-arrow-in-right',
        'logout': 'bi-box-arrow-right',
        'criar': 'bi-plus-circle',
        'editar': 'bi-pencil-square',
        'excluir': 'bi-trash',
        'importar': 'bi-upload',
        'disparar': 'bi-send',
        'acessar': 'bi-eye',
    }

    return icones.get(
        acao,
        'bi-circle'
    )


@register.filter
def money(valor):

    if valor is None:
        return '0,00'

    try:
        valor_decimal = Decimal(valor)
    except (InvalidOperation, TypeError, ValueError):
        return '0,00'

    return f'{valor_decimal:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


@register.filter
def cpf(valor):

    numeros = ''.join(
        filter(str.isdigit, str(valor or ''))
    )

    if len(numeros) != 11:
        return valor or ''

    return f'{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}'


@register.filter
def telefone(valor):

    numeros = ''.join(
        filter(str.isdigit, str(valor or ''))
    )

    if len(numeros) == 11:
        return f'({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}'

    if len(numeros) == 10:
        return f'({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}'

    return valor or ''


@register.simple_tag
def boolean_badge(valor):

    if valor:
        return 'Sim'

    return 'Não'


@register.simple_tag
def boolean_badge_class(valor):

    if valor:
        return 'bg-success'

    return 'bg-secondary'