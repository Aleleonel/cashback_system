from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER
from core.services import get_contexto_plataforma
from empresas.models import Matriz
from plataforma.forms import (
    WizardAdminForm,
    WizardLojaForm,
    WizardMatrizForm,
)
from plataforma.services import implantar_empresa
from plataforma.wizard import (
    get_dados_wizard_nova_empresa,
    get_senha_admin_wizard,
    limpar_wizard_nova_empresa,
    salvar_dados_wizard_nova_empresa,
    salvar_senha_admin_wizard,
)


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def nova_empresa_matriz(request):

    get_contexto_plataforma(request.user)

    dados_wizard = get_dados_wizard_nova_empresa(request)

    if request.method == 'POST':
        form = WizardMatrizForm(request.POST)

        if form.is_valid():
            salvar_dados_wizard_nova_empresa(
                request,
                'matriz',
                form.cleaned_data
            )

            return redirect('plataforma:nova_empresa_loja')

    else:
        form = WizardMatrizForm(
            initial=dados_wizard.get('matriz')
        )

    return render(
        request,
        'plataforma/wizard/matriz.html',
        {
            'form': form,
            'etapa': 1,
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def nova_empresa_loja(request):

    get_contexto_plataforma(request.user)

    dados_wizard = get_dados_wizard_nova_empresa(request)

    if 'matriz' not in dados_wizard:
        return redirect('plataforma:nova_empresa_matriz')

    if request.method == 'POST':
        form = WizardLojaForm(request.POST)

        if form.is_valid():
            salvar_dados_wizard_nova_empresa(
                request,
                'loja',
                form.cleaned_data
            )

            return redirect('plataforma:nova_empresa_admin')

    else:
        form = WizardLojaForm(
            initial=dados_wizard.get('loja')
        )

    return render(
        request,
        'plataforma/wizard/loja.html',
        {
            'form': form,
            'etapa': 2,
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def nova_empresa_admin(request):

    get_contexto_plataforma(request.user)

    dados_wizard = get_dados_wizard_nova_empresa(request)

    if 'matriz' not in dados_wizard:
        return redirect('plataforma:nova_empresa_matriz')

    if 'loja' not in dados_wizard:
        return redirect('plataforma:nova_empresa_loja')

    if request.method == 'POST':
        form = WizardAdminForm(request.POST)

        if form.is_valid():
            dados_admin = form.cleaned_data.copy()
            senha_admin = dados_admin.pop('password')

            salvar_dados_wizard_nova_empresa(
                request,
                'admin',
                dados_admin
            )

            salvar_senha_admin_wizard(
                request,
                senha_admin
            )

            return redirect('plataforma:nova_empresa_revisao')

    else:
        form = WizardAdminForm(
            initial=dados_wizard.get('admin')
        )

    return render(
        request,
        'plataforma/wizard/admin.html',
        {
            'form': form,
            'etapa': 3,
        }
    )


@login_required
@require_permission(PERMISSAO_PLATAFORMA_PAINEL_MASTER)
def nova_empresa_revisao(request):

    contexto = get_contexto_plataforma(request.user)

    dados_wizard = get_dados_wizard_nova_empresa(request)

    if 'matriz' not in dados_wizard:
        return redirect('plataforma:nova_empresa_matriz')

    if 'loja' not in dados_wizard:
        return redirect('plataforma:nova_empresa_loja')

    if 'admin' not in dados_wizard:
        return redirect('plataforma:nova_empresa_admin')

    if request.method == 'POST':

        cnpj_matriz = dados_wizard['matriz'].get('cnpj')

        if cnpj_matriz and Matriz.objects.filter(cnpj=cnpj_matriz).exists():
            messages.error(
                request,
                'Já existe uma matriz cadastrada com este CNPJ.'
            )

            return redirect('plataforma:nova_empresa_matriz')

        senha_admin = get_senha_admin_wizard(request)

        if not senha_admin:
            messages.error(
                request,
                'Senha do administrador não encontrada. Informe novamente os dados do administrador.'
            )

            return redirect('plataforma:nova_empresa_admin')

        resultado = implantar_empresa(
            dados_matriz=dados_wizard['matriz'],
            dados_loja=dados_wizard['loja'],
            dados_admin={
                **dados_wizard['admin'],
                'password': senha_admin,
            },
            usuario_executor=contexto['usuario'],
            request=request
        )

        messages.success(
            request,
            f"Empresa {resultado['matriz'].nome} implantada com sucesso."
        )

        limpar_wizard_nova_empresa(request)

        return redirect('plataforma:lista_matrizes')

    return render(
        request,
        'plataforma/wizard/revisao.html',
        {
            'dados': dados_wizard,
            'etapa': 4,
        }
    )