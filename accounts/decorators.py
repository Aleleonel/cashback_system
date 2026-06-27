from functools import wraps

from django.core.exceptions import PermissionDenied

from .services import usuario_tem_permissao


def require_permission(permissao):

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if not usuario_tem_permissao(
                request.user,
                permissao
            ):
                raise PermissionDenied(
                    'Você não tem permissão para acessar este recurso.'
                )

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator