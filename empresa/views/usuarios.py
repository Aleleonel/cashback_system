from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_EMPRESA_USUARIOS_GERENCIAR
from core.services import get_contexto_operacional_usuario
from empresa.forms import UsuarioEmpresaForm
from empresa.selectors import get_usuarios_empresa
from empresa.services import (
    alternar_status_usuario_empresa,
    criar_usuario_empresa,
    editar_usuario_empresa,
)


@login_required
@require_permission(PERMISSAO_EMPRESA_USUARIOS_GERENCIAR)
def lista_usuarios_empresa(request):

    contexto = get_contexto_operacional_usuario(request.user)

    busca = request.GET.get('q', '').strip()
    perfil = request.GET.get('perfil', '').strip()
    status = request.GET.get('status', '').strip()

    usuarios = get_usuarios_empresa(
        matriz=contexto['matriz'],
        busca=busca,
        perfil=perfil,
        status=status
    )

    paginator = Paginator(usuarios, 50)
    page = request.GET.get('page')
    usuarios = paginator.get_page(page)

    User = get_user_model()

    perfis_opcoes = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': perfil == valor,
        }
        for valor, nome in User.PERFIL_CHOICES
    ]

    status_opcoes = [
        {
            'valor': '',
            'nome': 'Todos',
            'selecionado': status == '',
        },
        {
            'valor': 'ativos',
            'nome': 'Ativos',
            'selecionado': status == 'ativos',
        },
        {
            'valor': 'inativos',
            'nome': 'Inativos',
            'selecionado': status == 'inativos',
        },
    ]

    return render(
        request,
        'empresa/lista_usuarios.html',
        {
            'usuarios': usuarios,
            'busca': busca,
            'perfil': perfil,
            'status': status,
            'perfis_opcoes': perfis_opcoes,
            'status_opcoes': status_opcoes,
        }
    )


@login_required
@require_permission(PERMISSAO_EMPRESA_USUARIOS_GERENCIAR)
def criar_usuario_empresa_view(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = UsuarioEmpresaForm(
            request.POST,
            matriz=contexto['matriz']
        )

        if form.is_valid():
            criar_usuario_empresa(
                matriz=contexto['matriz'],
                dados=form.cleaned_data,
                usuario_executor=request.user,
                request=request
            )

            messages.success(
                request,
                'Usuário criado com sucesso.'
            )

            return redirect('empresa:lista_usuarios')

    else:
        form = UsuarioEmpresaForm(
            matriz=contexto['matriz']
        )

    return render(
        request,
        'empresa/form_usuario.html',
        {
            'form': form,
            'titulo': 'Novo Usuário',
        }
    )


@login_required
@require_permission(PERMISSAO_EMPRESA_USUARIOS_GERENCIAR)
def editar_usuario_empresa_view(request, usuario_id):

    contexto = get_contexto_operacional_usuario(request.user)

    User = get_user_model()

    usuario = get_object_or_404(
        User.objects.prefetch_related('lojas'),
        id=usuario_id,
        matriz=contexto['matriz']
    )

    if request.method == 'POST':
        form = UsuarioEmpresaForm(
            request.POST,
            matriz=contexto['matriz'],
            usuario=usuario
        )

        if form.is_valid():
            editar_usuario_empresa(
                usuario=usuario,
                dados=form.cleaned_data,
                usuario_executor=request.user,
                request=request
            )

            messages.success(
                request,
                'Usuário atualizado com sucesso.'
            )

            return redirect('empresa:lista_usuarios')

    else:
        form = UsuarioEmpresaForm(
            matriz=contexto['matriz'],
            usuario=usuario,
            initial={
                'first_name': usuario.first_name,
                'username': usuario.username,
                'email': usuario.email,
                'telefone': usuario.telefone,
                'perfil': usuario.perfil,
                'lojas': usuario.lojas.all(),
                'ativo': usuario.ativo,
                'permissoes_extras': list(
                    usuario.permissoes_extras.values_list(
                        'permissao',
                        flat=True
                    )
                ),
            }
        )

    return render(
        request,
        'empresa/form_usuario.html',
        {
            'form': form,
            'titulo': 'Editar Usuário',
            'usuario_obj': usuario,
        }
    )


@login_required
@require_permission(PERMISSAO_EMPRESA_USUARIOS_GERENCIAR)
def alternar_status_usuario_empresa_view(request, usuario_id):

    contexto = get_contexto_operacional_usuario(request.user)

    User = get_user_model()

    usuario = get_object_or_404(
        User,
        id=usuario_id,
        matriz=contexto['matriz']
    )

    alternar_status_usuario_empresa(
        usuario=usuario,
        usuario_executor=request.user,
        request=request
    )

    messages.success(
        request,
        'Status do usuário atualizado com sucesso.'
    )

    return redirect('empresa:lista_usuarios')