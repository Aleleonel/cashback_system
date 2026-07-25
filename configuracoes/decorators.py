from functools import wraps

from django.contrib.auth.views import redirect_to_login

from .access import (
    validar_acesso_central_configuracoes,
    validar_acesso_configuracoes_criticas,
)


def central_configuracoes_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        request.contexto_configuracoes = (
            validar_acesso_central_configuracoes(usuario=request.user)
        )
        return view_func(request, *args, **kwargs)

    return wrapper


def configuracoes_criticas_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        request.contexto_configuracoes = (
            validar_acesso_configuracoes_criticas(usuario=request.user)
        )
        return view_func(request, *args, **kwargs)

    return wrapper
