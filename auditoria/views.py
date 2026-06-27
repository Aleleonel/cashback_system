from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER

from .selectors import get_registros_auditoria


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def lista_auditoria(request):

    registros = get_registros_auditoria()

    paginator = Paginator(registros, 50)

    page = request.GET.get('page')

    registros = paginator.get_page(page)

    return render(
        request,
        'auditoria/lista_auditoria.html',
        {
            'registros': registros,
        }
    )