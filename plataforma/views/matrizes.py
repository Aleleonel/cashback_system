from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER
from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from core.choices import StatusOperacional
from core.services import get_contexto_plataforma
from empresas.models import Matriz
from plataforma.forms import MatrizForm
from plataforma.selectors import get_matrizes_plataforma


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
        {'valor': '', 'nome': 'Todas', 'selecionado': status == ''},
        {'valor': StatusOperacional.IMPLANTACAO, 'nome': 'Em implantação', 'selecionado': status == StatusOperacional.IMPLANTACAO},
        {'valor': StatusOperacional.ATIVA, 'nome': 'Ativas', 'selecionado': status == StatusOperacional.ATIVA},
        {'valor': StatusOperacional.SUSPENSA, 'nome': 'Suspensas', 'selecionado': status == StatusOperacional.SUSPENSA},
        {'valor': StatusOperacional.BLOQUEADA, 'nome': 'Bloqueadas', 'selecionado': status == StatusOperacional.BLOQUEADA},
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

            messages.success(request, 'Matriz criada com sucesso.')

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

            messages.success(request, 'Matriz atualizada com sucesso.')

            return redirect('plataforma:lista_matrizes')

    else:
        form = MatrizForm(instance=matriz)

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

    if matriz.status == StatusOperacional.ATIVA:
        matriz.status = StatusOperacional.SUSPENSA
        status = 'suspensa'
    else:
        matriz.status = StatusOperacional.ATIVA
        status = 'ativada'

    matriz.save(update_fields=['status'])

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