from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services import get_contexto_operacional_usuario

from .selectors import get_dashboard_resumo


@login_required
def dashboard(request):

    contexto = get_contexto_operacional_usuario(
        request.user
    )

    resumo = get_dashboard_resumo(
        matriz=contexto['matriz']
    )

    return render(
        request,
        'relatorios/dashboard.html',
        {
            'resumo': resumo,
        }
    )