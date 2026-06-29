from django.contrib.auth.decorators import login_required
from accounts.decorators import require_permission
from core.choices import StatusOperacional

from .selectors import (
    get_resumo_painel_master, 
    get_matrizes_plataforma,
    get_lojas_plataforma,
)

from django.core.paginator import Paginator

from core.services import get_contexto_plataforma
from auditoria.services import registrar_auditoria

from .services import (
    alternar_status_loja_plataforma,
    criar_loja_plataforma,
    editar_loja_plataforma,
    implantar_empresa,
)


from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.permissions import PERMISSAO_PLATAFORMA_PAINEL_MASTER
from auditoria.models import RegistroAuditoria

from empresas.models import Loja, Matriz

from .wizard import (
    get_dados_wizard_nova_empresa,
    limpar_wizard_nova_empresa,
    salvar_dados_wizard_nova_empresa,
    get_senha_admin_wizard,
    salvar_senha_admin_wizard,
)


from .forms import (
    LojaForm,
    MatrizForm,
    WizardAdminForm,
    WizardLojaForm,
    WizardMatrizForm,
)

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
            'valor': StatusOperacional.IMPLANTACAO,
            'nome': 'Em implantação',
            'selecionado': status == StatusOperacional.IMPLANTACAO,
        },
        {
            'valor': StatusOperacional.ATIVA,
            'nome': 'Ativas',
            'selecionado': status == StatusOperacional.ATIVA,
        },
        {
            'valor': StatusOperacional.SUSPENSA,
            'nome': 'Suspensas',
            'selecionado': status == StatusOperacional.SUSPENSA,
        },
        {
            'valor': StatusOperacional.BLOQUEADA,
            'nome': 'Bloqueadas',
            'selecionado': status == StatusOperacional.BLOQUEADA,
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
        {
            'valor': '',
            'nome': 'Todas',
            'selecionado': status == '',
        },
        {
            'valor': StatusOperacional.IMPLANTACAO,
            'nome': 'Em implantação',
            'selecionado': status == StatusOperacional.IMPLANTACAO,
        },
        {
            'valor': StatusOperacional.ATIVA,
            'nome': 'Ativas',
            'selecionado': status == StatusOperacional.ATIVA,
        },
        {
            'valor': StatusOperacional.SUSPENSA,
            'nome': 'Suspensas',
            'selecionado': status == StatusOperacional.SUSPENSA,
        },
        {
            'valor': StatusOperacional.BLOQUEADA,
            'nome': 'Bloqueadas',
            'selecionado': status == StatusOperacional.BLOQUEADA,
        },
        {
            'valor': StatusOperacional.ENCERRADA,
            'nome': 'Encerradas',
            'selecionado': status == StatusOperacional.ENCERRADA,
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
        form = LojaForm(
            instance=loja
        )

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