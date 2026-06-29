from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.services import get_contexto_operacional_usuario

from .selectors import get_dashboard_resumo

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_RELATORIOS_DASHBOARD


@login_required
@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)
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