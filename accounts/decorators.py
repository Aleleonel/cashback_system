from functools import wraps

from django.core.exceptions import PermissionDenied

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from .services import usuario_tem_permissao


def require_permission(permissao):

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if not usuario_tem_permissao(
                request.user,
                permissao
            ):
                usuario = (
                    request.user
                    if getattr(
                        request.user,
                        'is_authenticated',
                        False
                    )
                    else None
                )

                matriz = (
                    getattr(request.user, 'matriz', None)
                    if usuario
                    else None
                )

                registrar_auditoria(
                    usuario=usuario,
                    matriz=matriz,
                    loja=None,
                    acao=RegistroAuditoria.ACAO_ACESSAR,
                    recurso='acesso.negado',
                    descricao=(
                        f'Acesso negado. '
                        f'Permissão exigida: {permissao}. '
                        f'View: {view_func.__name__}.'
                    ),
                    request=request
                )

                raise PermissionDenied(
                    'Você não tem permissão para acessar este recurso.'
                )

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
