from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import require_permission
from accounts.services import PERMISSAO_PLATAFORMA_PAINEL_MASTER

from .selectors import (
    get_resumo_painel_master, 
    get_matrizes_plataforma,
)

from django.core.paginator import Paginator

from core.services import get_contexto_plataforma

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


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def lista_matrizes(request):

    get_contexto_plataforma(request.user)

    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    matrizes = get_matrizes_plataforma(
        busca=busca,
        status=status
    )

    paginator = Paginator(matrizes, 50)

    page = request.GET.get('page')

    matrizes = paginator.get_page(page)

    status_opcoes = [
        {
            'valor': '',
            'nome': 'Todas',
            'selecionado': status == '',
        },
        {
            'valor': 'ativas',
            'nome': 'Ativas',
            'selecionado': status == 'ativas',
        },
        {
            'valor': 'inativas',
            'nome': 'Inativas',
            'selecionado': status == 'inativas',
        },
    ]

    return render(
        request,
        'plataforma/lista_matrizes.html',
        {
            'matrizes': matrizes,
            'busca': busca,
            'status': status,
            'status_opcoes': status_opcoes,
        }
    )