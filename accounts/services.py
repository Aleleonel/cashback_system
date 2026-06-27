from django.core.exceptions import PermissionDenied

from .permissions import (
    PERMISSAO_PLATAFORMA_PAINEL_MASTER,
    PERMISSOES_POR_PERFIL,
)


def usuario_tem_permissao(usuario, permissao):
    if not usuario.is_authenticated:
        return False

    if usuario.is_superuser:
        return True

    if permissao == PERMISSAO_PLATAFORMA_PAINEL_MASTER:
        return False

    if not getattr(usuario, 'ativo', False):
        return False

    permissoes = PERMISSOES_POR_PERFIL.get(
        usuario.perfil,
        set()
    )

    return permissao in permissoes


def exigir_permissao(usuario, permissao):
    if not usuario_tem_permissao(usuario, permissao):
        raise PermissionDenied(
            'Você não tem permissão para acessar este recurso.'
        )