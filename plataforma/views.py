from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.services import PERMISSAO_PLATAFORMA_PAINEL_MASTER

from .selectors import get_resumo_painel_master


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def painel_master(request):

    resumo = get_resumo_painel_master()

    return render(
        request,
        'plataforma/painel_master.html',
        {
            'resumo': resumo,
        }
    )