from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_EMPRESA_LOJAS_GERENCIAR
from core.choices import StatusOperacional
from core.services import get_contexto_operacional_usuario
from empresa.forms import ConfiguracaoFiscalLojaEmpresaForm, LojaEmpresaForm
from empresa.selectors import get_lojas_empresa
from empresa.services import (
    alternar_status_loja_empresa,
    criar_loja_empresa,
    editar_loja_empresa,
    salvar_configuracao_fiscal_loja_empresa,
)
from empresas.models import Loja
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from empresa.services import avaliar_prontidao_fiscal_loja


@login_required
@require_permission(PERMISSAO_EMPRESA_LOJAS_GERENCIAR)
def lista_lojas_empresa(request):

    contexto = get_contexto_operacional_usuario(request.user)

    busca = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    lojas = get_lojas_empresa(
        matriz=contexto['matriz'],
        busca=busca,
        status=status
    )

    for loja in lojas:
        prontidao = avaliar_prontidao_fiscal_loja(loja)
        loja.prontidao_fiscal_status = prontidao["status"]
        loja.prontidao_fiscal_label = prontidao["label"]
        loja.prontidao_fiscal_detalhe = prontidao["detalhe"]
        loja.prontidao_fiscal_pendencias = prontidao["pendencias"]

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

    return render(
        request,
        'empresa/lista_lojas.html',
        {
            'lojas': lojas,
            'busca': busca,
            'status': status,
            'status_opcoes': status_opcoes,
        }
    )


@login_required
@require_permission(PERMISSAO_EMPRESA_LOJAS_GERENCIAR)
def criar_loja_empresa_view(request):

    contexto = get_contexto_operacional_usuario(request.user)

    configurar_fiscal = request.method == 'POST' and request.POST.get('configurar_fiscal') == '1'

    if request.method == 'POST':
        form = LojaEmpresaForm(request.POST, matriz=contexto['matriz'])
        fiscal_form = ConfiguracaoFiscalLojaEmpresaForm(request.POST) if configurar_fiscal else ConfiguracaoFiscalLojaEmpresaForm()
        fiscal_valido = fiscal_form.is_valid() if configurar_fiscal else True

        if form.is_valid() and fiscal_valido:
            with transaction.atomic():
                loja = criar_loja_empresa(
                    matriz=contexto['matriz'], dados=form.cleaned_data,
                    usuario_executor=request.user, request=request
                )
                if configurar_fiscal:
                    salvar_configuracao_fiscal_loja_empresa(
                        loja=loja, dados=fiscal_form.cleaned_data,
                        usuario_executor=request.user, request=request
                    )
            messages.success(
                request,
                'Loja e configuracao fiscal criadas com sucesso.' if configurar_fiscal
                else 'Loja criada com sucesso. A configuracao fiscal permanece incompleta.'
            )
            return redirect('empresa:lista_lojas')
    else:
        form = LojaEmpresaForm(matriz=contexto['matriz'])
        fiscal_form = ConfiguracaoFiscalLojaEmpresaForm()

    return render(
        request, 'empresa/form_loja.html',
        {
            'form': form, 'fiscal_form': fiscal_form,
            'configurar_fiscal': configurar_fiscal,
            'configuracao_fiscal_existente': False,
            'titulo': 'Nova Loja',
        }
    )


@login_required
@require_permission(PERMISSAO_EMPRESA_LOJAS_GERENCIAR)
def editar_loja_empresa_view(request, loja_id):

    contexto = get_contexto_operacional_usuario(request.user)

    loja = get_object_or_404(
        Loja,
        id=loja_id,
        matriz=contexto['matriz']
    )

    try:
        configuracao_fiscal = loja.configuracao_emissao_fiscal
    except ConfiguracaoEmissaoFiscalLoja.DoesNotExist:
        configuracao_fiscal = None

    configuracao_fiscal_existente = configuracao_fiscal is not None
    configurar_fiscal = configuracao_fiscal_existente or (
        request.method == 'POST' and request.POST.get('configurar_fiscal') == '1'
    )

    if request.method == 'POST':
        form = LojaEmpresaForm(request.POST, instance=loja, matriz=contexto['matriz'])
        fiscal_form = (
            ConfiguracaoFiscalLojaEmpresaForm(request.POST, instance=configuracao_fiscal)
            if configurar_fiscal else ConfiguracaoFiscalLojaEmpresaForm()
        )
        fiscal_valido = fiscal_form.is_valid() if configurar_fiscal else True

        if form.is_valid() and fiscal_valido:
            with transaction.atomic():
                editar_loja_empresa(
                    loja=loja, dados=form.cleaned_data,
                    usuario_executor=request.user, request=request
                )
                if configurar_fiscal:
                    salvar_configuracao_fiscal_loja_empresa(
                        loja=loja, dados=fiscal_form.cleaned_data,
                        usuario_executor=request.user, request=request
                    )
            messages.success(
                request,
                'Loja e configuracao fiscal atualizadas com sucesso.' if configurar_fiscal
                else 'Loja atualizada. A configuracao fiscal permanece incompleta.'
            )
            return redirect('empresa:lista_lojas')
    else:
        form = LojaEmpresaForm(instance=loja, matriz=contexto['matriz'])
        fiscal_form = ConfiguracaoFiscalLojaEmpresaForm(instance=configuracao_fiscal)

    return render(
        request, 'empresa/form_loja.html',
        {
            'form': form, 'fiscal_form': fiscal_form,
            'configurar_fiscal': configurar_fiscal,
            'configuracao_fiscal_existente': configuracao_fiscal_existente,
            'titulo': 'Editar Loja', 'loja': loja,
        }
    )


@login_required
@require_permission(PERMISSAO_EMPRESA_LOJAS_GERENCIAR)
def alternar_status_loja_empresa_view(request, loja_id):

    contexto = get_contexto_operacional_usuario(request.user)

    loja = get_object_or_404(
        Loja,
        id=loja_id,
        matriz=contexto['matriz']
    )

    alternar_status_loja_empresa(
        loja=loja,
        usuario_executor=request.user,
        request=request
    )

    messages.success(
        request,
        'Status da loja atualizado com sucesso.'
    )

    return redirect('empresa:lista_lojas')