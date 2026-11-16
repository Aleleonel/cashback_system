from django import template
from accounts.permissions import PERMISSAO_ATACADO_VISUALIZAR
from accounts.services import usuario_tem_permissao

register = template.Library()

@register.simple_tag
def pode_visualizar_atacado(usuario):
    return usuario_tem_permissao(usuario, PERMISSAO_ATACADO_VISUALIZAR)
