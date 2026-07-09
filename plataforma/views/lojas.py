from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER
from core.choices import StatusOperacional
from core.services import get_contexto_plataforma
from empresas.models import Loja, Matriz
from plataforma.forms import LojaForm
from plataforma.selectors import get_lojas_plataforma
from plataforma.services import (
    alternar_status_loja_plataforma,
    criar_loja_plataforma,
    editar_loja_plataforma,
)


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def lista_lojas(request):

    get_contexto_plataforma(request.user)

    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    matriz_id = request.GET.get('matriz', '').strip()

    lojas = get_lojas_plataforma(
        busca=busca,
        status=status,
        matriz_id=matriz_id
    )

    matrizes = Matriz.objects.filter(
        status=StatusOperacional.ATIVA
    ).order_by(
        'nome'
    )

    paginator = Paginator(lojas, 50)
    page = request.GET.get('page')
    lojas = paginator.get_page(page)

    status_opcoes = [
        {'valor': '', 'nome': 'Todas', 'selecionado': status == ''},
        {'valor': StatusOperacional.IMPLANTACAO, 'nome': 'Em implantação', 'selecionado': status == StatusOperacional.IMPLANTACAO},
        {'valor': StatusOperacional.ATIVA, 'nome': 'Ativas', 'selecionado': status == StatusOperacional.ATIVA},
        {'valor': StatusOperacional.SUSPENSA, 'nome': 'Suspensas', 'selecionado': status == StatusOperacional.SUSPENSA},
        {'valor': StatusOperacional.BLOQUEADA, 'nome': 'Bloqueadas', 'selecionado': status == StatusOperacional.BLOQUEADA},
        {'valor': StatusOperacional.ENCERRADA, 'nome': 'Encerradas', 'selecionado': status == StatusOperacional.ENCERRADA},
    ]

    matrizes_opcoes = [
        {
            'valor': matriz.id,
            'nome': matriz.nome,
            'selecionado': str(matriz.id) == matriz_id,
        }
        for matriz in matrizes
    ]

    return render(
        request,
        'plataforma/lista_lojas.html',
        {
            'lojas': lojas,
            'busca': busca,
            'status': status,
            'matriz_id': matriz_id,
            'status_opcoes': status_opcoes,
            'matrizes_opcoes': matrizes_opcoes,
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def criar_loja(request):

    contexto = get_contexto_plataforma(request.user)

    if request.method == 'POST':
        form = LojaForm(request.POST)

        if form.is_valid():
            criar_loja_plataforma(
                dados=form.cleaned_data,
                usuario_executor=contexto['usuario'],
                request=request
            )

            messages.success(
                request,
                'Loja criada com sucesso.'
            )

            return redirect('plataforma:lista_lojas')

    else:
        form = LojaForm()

    return render(
        request,
        'plataforma/form_loja.html',
        {
            'form': form,
            'titulo': 'Nova Loja',
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def editar_loja(request, loja_id):

    contexto = get_contexto_plataforma(request.user)

    loja = get_object_or_404(
        Loja.objects.select_related('matriz'),
        id=loja_id
    )

    if request.method == 'POST':
        form = LojaForm(
            request.POST,
            instance=loja
        )

        if form.is_valid():
            editar_loja_plataforma(
                loja=loja,
                dados=form.cleaned_data,
                usuario_executor=contexto['usuario'],
                request=request
            )

            messages.success(
                request,
                'Loja atualizada com sucesso.'
            )

            return redirect('plataforma:lista_lojas')

    else:
        form = LojaForm(instance=loja)

    return render(
        request,
        'plataforma/form_loja.html',
        {
            'form': form,
            'titulo': 'Editar Loja',
            'loja': loja,
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def alternar_status_loja(request, loja_id):

    contexto = get_contexto_plataforma(request.user)

    loja = get_object_or_404(
        Loja.objects.select_related('matriz'),
        id=loja_id
    )

    alternar_status_loja_plataforma(
        loja=loja,
        usuario_executor=contexto['usuario'],
        request=request
    )

    messages.success(
        request,
        'Status da loja atualizado com sucesso.'
    )

    return redirect('plataforma:lista_lojas')