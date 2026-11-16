"""View do dashboard de estoque."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services import get_contexto_operacional_usuario
from accounts.services import exigir_permissao
from accounts.permissions import PERMISSAO_ESTOQUE_VISUALIZAR
from estoque.selectors.dashboard import (
    get_indicadores_dashboard_estoque,
)


@login_required
def dashboard_estoque(request):
    exigir_permissao(request.user, PERMISSAO_ESTOQUE_VISUALIZAR)
    # Dashboard consolidado: nao expor dados de outras lojas a operadores.
    from django.core.exceptions import PermissionDenied
    if getattr(request.user, "perfil", None) == "operador":
        raise PermissionDenied("Dashboard consolidado indisponivel para operador.")
    contexto = get_contexto_operacional_usuario(request.user)
    matriz = contexto['matriz']

    indicadores = get_indicadores_dashboard_estoque(
        matriz=matriz,
    )

    return render(
        request,
        'estoque/dashboard.html',
        {
            'indicadores': indicadores,
        },
    )