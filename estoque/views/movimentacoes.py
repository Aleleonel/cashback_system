"""Views relacionadas às movimentações de estoque."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from core.services import get_contexto_operacional_usuario
from estoque.selectors import get_movimentacoes


@login_required
def lista_movimentacoes(request):
    contexto = get_contexto_operacional_usuario(
        request.user
    )

    busca = request.GET.get(
        'busca',
        ''
    ).strip()

    movimentacoes = get_movimentacoes(
        matriz=contexto['matriz'],
        busca=busca,
    )

    paginador = Paginator(
        movimentacoes,
        25
    )

    pagina = paginador.get_page(
        request.GET.get('page')
    )

    return render(
        request,
        'estoque/movimentacoes/lista.html',
        {
            'pagina': pagina,
            'busca': busca,
        }
    )