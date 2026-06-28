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