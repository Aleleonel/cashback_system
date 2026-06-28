from django.contrib.auth.decorators import login_required
from accounts.decorators import require_permission
from .selectors import (
    get_resumo_painel_master, 
    get_matrizes_plataforma,
    get_lojas_plataforma,
)

from django.core.paginator import Paginator
from core.services import get_contexto_plataforma


from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from empresas.models import Matriz
from .forms import MatrizForm


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


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def criar_matriz(request):

    contexto = get_contexto_plataforma(request.user)

    if request.method == 'POST':
        form = MatrizForm(request.POST)

        if form.is_valid():
            matriz = form.save()

            registrar_auditoria(
                usuario=contexto['usuario'],
                matriz=matriz,
                loja=None,
                acao=RegistroAuditoria.ACAO_CRIAR,
                recurso='plataforma.matriz',
                recurso_id=matriz.id,
                descricao=f'Matriz criada: {matriz.nome}',
                request=request
            )

            messages.success(
                request,
                'Matriz criada com sucesso.'
            )

            return redirect('plataforma:lista_matrizes')

    else:
        form = MatrizForm()

    return render(
        request,
        'plataforma/form_matriz.html',
        {
            'form': form,
            'titulo': 'Nova Matriz',
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def editar_matriz(request, matriz_id):

    contexto = get_contexto_plataforma(request.user)

    matriz = get_object_or_404(
        Matriz,
        id=matriz_id
    )

    if request.method == 'POST':
        form = MatrizForm(
            request.POST,
            instance=matriz
        )

        if form.is_valid():
            matriz = form.save()

            registrar_auditoria(
                usuario=contexto['usuario'],
                matriz=matriz,
                loja=None,
                acao=RegistroAuditoria.ACAO_EDITAR,
                recurso='plataforma.matriz',
                recurso_id=matriz.id,
                descricao=f'Matriz editada: {matriz.nome}',
                request=request
            )

            messages.success(
                request,
                'Matriz atualizada com sucesso.'
            )

            return redirect('plataforma:lista_matrizes')

    else:
        form = MatrizForm(
            instance=matriz
        )

    return render(
        request,
        'plataforma/form_matriz.html',
        {
            'form': form,
            'titulo': 'Editar Matriz',
            'matriz': matriz,
        }
    )

@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def alternar_status_matriz(request, matriz_id):

    contexto = get_contexto_plataforma(request.user)

    matriz = get_object_or_404(
        Matriz,
        id=matriz_id
    )

    matriz.ativa = not matriz.ativa
    matriz.save(update_fields=['ativa'])

    status = 'ativada' if matriz.ativa else 'inativada'

    registrar_auditoria(
        usuario=contexto['usuario'],
        matriz=matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='plataforma.matriz',
        recurso_id=matriz.id,
        descricao=f'Matriz {status}: {matriz.nome}',
        request=request
    )

    messages.success(
        request,
        f'Matriz {status} com sucesso.'
    )

    return redirect('plataforma:lista_matrizes')


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
        ativa=True
    ).order_by(
        'nome'
    )

    paginator = Paginator(lojas, 50)

    page = request.GET.get('page')

    lojas = paginator.get_page(page)

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