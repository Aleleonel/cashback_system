from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_DASHBOARD
from core.services import get_contexto_operacional_usuario

from empresa.selectors import get_resumo_minha_empresa


@login_required
@require_permission(PERMISSAO_DASHBOARD)
def dashboard_empresa(request):

    contexto = get_contexto_operacional_usuario(request.user)

    resumo = get_resumo_minha_empresa(
        matriz=contexto['matriz']
    )

    return render(
        request,
        'empresa/dashboard.html',
        {
            'resumo': resumo,
            'matriz': contexto['matriz'],
        }
    )