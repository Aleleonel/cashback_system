from django.contrib.auth.views import LoginView
from django.urls import reverse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.forms import UsuarioPlataformaForm
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER
from accounts.selectors import get_usuarios_plataforma
from accounts.services import (
    alternar_status_usuario_plataforma,
    criar_usuario_plataforma,
    editar_usuario_plataforma,
)
from core.services import get_contexto_plataforma
from empresas.models import Matriz


class CashbackLoginView(LoginView):

    template_name = 'registration/login.html'

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse('plataforma:painel_master')

        return reverse('relatorios:dashboard')


    @login_required
    @require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
    def lista_usuarios(request):

        get_contexto_plataforma(request.user)

        busca = request.GET.get('q', '').strip()
        perfil = request.GET.get('perfil', '').strip()
        status = request.GET.get('status', '').strip()
        matriz_id = request.GET.get('matriz', '').strip()

        usuarios = get_usuarios_plataforma(
            busca=busca,
            perfil=perfil,
            status=status,
            matriz_id=matriz_id
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

        matrizes = Matriz.objects.order_by('nome')

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
            'accounts/lista_usuarios.html',
            {
                'usuarios': usuarios,
                'busca': busca,
                'perfil': perfil,
                'status': status,
                'matriz_id': matriz_id,
                'perfis_opcoes': perfis_opcoes,
                'status_opcoes': status_opcoes,
                'matrizes_opcoes': matrizes_opcoes,
            }
        )


    @login_required
    @require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
    def criar_usuario(request):

        contexto = get_contexto_plataforma(request.user)

        if request.method == 'POST':
            form = UsuarioPlataformaForm(request.POST)

            if form.is_valid():
                criar_usuario_plataforma(
                    dados=form.cleaned_data,
                    usuario_executor=contexto['usuario'],
                    request=request
                )

                messages.success(
                    request,
                    'Usuário criado com sucesso.'
                )

                return redirect('accounts:lista_usuarios')

        else:
            form = UsuarioPlataformaForm()

        return render(
            request,
            'accounts/form_usuario.html',
            {
                'form': form,
                'titulo': 'Novo Usuário',
            }
        )


    @login_required
    @require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
    def editar_usuario(request, usuario_id):

        contexto = get_contexto_plataforma(request.user)

        User = get_user_model()

        usuario = get_object_or_404(
            User.objects.select_related('matriz').prefetch_related('lojas'),
            id=usuario_id
        )

        if request.method == 'POST':
            form = UsuarioPlataformaForm(
                request.POST,
                usuario=usuario
            )

            if form.is_valid():
                editar_usuario_plataforma(
                    usuario=usuario,
                    dados=form.cleaned_data,
                    usuario_executor=contexto['usuario'],
                    request=request
                )

                messages.success(
                    request,
                    'Usuário atualizado com sucesso.'
                )

                return redirect('accounts:lista_usuarios')

        else:
            form = UsuarioPlataformaForm(
                usuario=usuario,
                initial={
                    'first_name': usuario.first_name,
                    'username': usuario.username,
                    'email': usuario.email,
                    'telefone': usuario.telefone,
                    'perfil': usuario.perfil,
                    'matriz': usuario.matriz,
                    'lojas': usuario.lojas.all(),
                    'ativo': usuario.ativo,
                }
            )

        return render(
            request,
            'accounts/form_usuario.html',
            {
                'form': form,
                'titulo': 'Editar Usuário',
                'usuario_obj': usuario,
            }
        )


    @login_required
    @require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
    def alternar_status_usuario(request, usuario_id):

        contexto = get_contexto_plataforma(request.user)

        User = get_user_model()

        usuario = get_object_or_404(
            User.objects.select_related('matriz'),
            id=usuario_id
        )

        alternar_status_usuario_plataforma(
            usuario=usuario,
            usuario_executor=contexto['usuario'],
            request=request
        )

        messages.success(
            request,
            'Status do usuário atualizado com sucesso.'
        )

        return redirect('accounts:lista_usuarios')