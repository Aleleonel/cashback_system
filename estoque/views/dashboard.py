"""View do dashboard de estoque."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services import get_contexto_operacional_usuario
from estoque.selectors.dashboard import (
    get_indicadores_dashboard_estoque,
)


@login_required
def dashboard_estoque(request):
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