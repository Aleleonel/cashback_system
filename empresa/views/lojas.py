from dataclasses import dataclass

from fiscal.services_certificado_a1 import CertificadoA1Error
from django.core.exceptions import ValidationError
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
from fiscal.services_armazenamento_certificado_a1 import armazenar_certificado_a1, remover_certificado_a1_por_referencia
from fiscal.services_secrets_certificado_a1 import (
    SegredoCertificadoA1Error,
    armazenar_senha_certificado_a1,
    remover_senha_certificado_a1,
)
from empresa.services import avaliar_prontidao_fiscal_loja



# 195F3NQ_A1_VIEW
@dataclass(frozen=True)
class UploadA1Persistido:
    referencia_certificado: str | None
    referencia_segredo: str | None


def _remover_upload_a1_persistido(upload):
    if upload.referencia_certificado:
        remover_certificado_a1_por_referencia(upload.referencia_certificado)
    if upload.referencia_segredo:
        remover_senha_certificado_a1(upload.referencia_segredo)


def _persistir_upload_a1_se_informado(*, loja, fiscal_form):
    arquivo = fiscal_form.cleaned_data.get('certificado_a1_arquivo')
    if not arquivo:
        return UploadA1Persistido(None, None)

    senha = fiscal_form.cleaned_data.get('certificado_a1_senha')
    cfg = ConfiguracaoEmissaoFiscalLoja.objects.get(loja=loja)
    certificado_anterior = str(cfg.certificado_a1_referencia or '').strip()
    segredo_anterior = str(
        cfg.certificado_a1_segredo_referencia or ''
    ).strip()
    novo_certificado = armazenar_certificado_a1(
        loja_id=loja.pk,
        arquivo=arquivo,
        senha=senha,
    )
    try:
        novo_segredo = armazenar_senha_certificado_a1(
            loja_id=loja.pk,
            senha=senha,
        )
    except Exception:
        remover_certificado_a1_por_referencia(novo_certificado)
        raise

    try:
        cfg.certificado_a1_referencia = novo_certificado
        cfg.certificado_a1_segredo_referencia = novo_segredo
        cfg.full_clean()
        cfg.save(update_fields=[
            'certificado_a1_referencia',
            'certificado_a1_segredo_referencia',
            'atualizado_em',
        ])
    except Exception:
        remover_certificado_a1_por_referencia(novo_certificado)
        remover_senha_certificado_a1(novo_segredo)
        raise

    if certificado_anterior and certificado_anterior != novo_certificado:
        transaction.on_commit(
            lambda referencia=certificado_anterior:
            remover_certificado_a1_por_referencia(referencia)
        )
    if segredo_anterior and segredo_anterior != novo_segredo:
        transaction.on_commit(
            lambda referencia=segredo_anterior:
            remover_senha_certificado_a1(referencia)
        )
    return UploadA1Persistido(novo_certificado, novo_segredo)

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
        fiscal_form = ConfiguracaoFiscalLojaEmpresaForm(request.POST, request.FILES) if configurar_fiscal else ConfiguracaoFiscalLojaEmpresaForm()
        fiscal_valido = fiscal_form.is_valid() if configurar_fiscal else True

        if form.is_valid() and fiscal_valido:
            upload_a1_persistido = UploadA1Persistido(None, None)
            try:
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
                        upload_a1_persistido = _persistir_upload_a1_se_informado(loja=loja, fiscal_form=fiscal_form)
            except (ValidationError, CertificadoA1Error, SegredoCertificadoA1Error) as exc:
                _remover_upload_a1_persistido(upload_a1_persistido)
                fiscal_form.add_error('certificado_a1_arquivo', str(exc))
            except Exception:
                _remover_upload_a1_persistido(upload_a1_persistido)
                raise
            else:
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
            ConfiguracaoFiscalLojaEmpresaForm(request.POST, request.FILES, instance=configuracao_fiscal)
            if configurar_fiscal else ConfiguracaoFiscalLojaEmpresaForm()
        )
        fiscal_valido = fiscal_form.is_valid() if configurar_fiscal else True

        if form.is_valid() and fiscal_valido:
            upload_a1_persistido = UploadA1Persistido(None, None)
            try:
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
                        upload_a1_persistido = _persistir_upload_a1_se_informado(loja=loja, fiscal_form=fiscal_form)
            except (ValidationError, CertificadoA1Error, SegredoCertificadoA1Error) as exc:
                _remover_upload_a1_persistido(upload_a1_persistido)
                fiscal_form.add_error('certificado_a1_arquivo', str(exc))
            except Exception:
                _remover_upload_a1_persistido(upload_a1_persistido)
                raise
            else:
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