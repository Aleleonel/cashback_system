from django.shortcuts import get_object_or_404
from django.urls import reverse
from campanhas.utils import get_template_json_placeholder, get_template_json_url_placeholder

from clientes.models import Cliente
from django.contrib.auth.decorators import login_required

from accounts.decorators import require_permission

from accounts.permissions import (
    PERMISSAO_CAMPANHAS_DISPARAR,
    PERMISSAO_CAMPANHAS_CONFIGURAR,
    PERMISSAO_CAMPANHAS_TEMPLATES,
)

from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import models
from core.services import get_contexto_operacional_usuario
from clientes.selectors import aplicar_busca_clientes
from django.http import JsonResponse
from clientes.utils import limpar_numero, normalizar_texto

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from .selectors import (
    get_aniversariantes_do_mes,
    get_historico_envios_aniversario,
    get_fila_envios_aniversario,
    get_configuracao_campanha_aniversario,
    get_templates_campanhas,
)

from django.contrib import messages
from django.shortcuts import redirect

from .forms import (
    DisparoAniversariantesForm, 
    ConfiguracaoCampanhaAniversarioForm,
    TemplateCampanhaForm,
)

from .models import ( 
    CampanhaAniversarioEnvio,
    TemplateCampanha,
)

from .services import (
    registrar_disparos_aniversariantes, 
    registrar_reenvio_aniversariante,
    renderizar_mensagem_template,
    get_contexto_exemplo_template,
    
)


@login_required
@require_permission(PERMISSAO_CAMPANHAS_DISPARAR)
def aniversariantes_mes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    aniversariantes = get_aniversariantes_do_mes(
        matriz=contexto['matriz']
    )

    configuracao = get_configuracao_campanha_aniversario(
        matriz=contexto['matriz']
    )

    busca = request.GET.get('q', '').strip()

    if busca:
        aniversariantes = aplicar_busca_clientes(
            aniversariantes,
            busca
        )

    total_aniversariantes = aniversariantes.count()

    total_enviados = aniversariantes.filter(
        campanha_enviada=True
    ).count()

    total_pendentes = (
        total_aniversariantes - total_enviados
    )

    paginator = Paginator(aniversariantes, 50)

    page = request.GET.get('page')

    aniversariantes = paginator.get_page(page)

    return render(
        request,
        'campanhas/aniversariantes_mes.html',
        {
            'aniversariantes': aniversariantes,
            'busca': busca,
            'total_aniversariantes': total_aniversariantes,
            'total_enviados': total_enviados,
            'total_pendentes': total_pendentes,
            'configuracao': configuracao,
        }
    )

@login_required
@require_permission(PERMISSAO_CAMPANHAS_DISPARAR)
def disparar_aniversariantes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    clientes = get_aniversariantes_do_mes(
        matriz=contexto['matriz']
    )

    configuracao = get_configuracao_campanha_aniversario(
        matriz=contexto['matriz']
    )

    if not configuracao.ativa:
        messages.warning(
            request,
            'A campanha de aniversário está desativada. Ative a campanha nas configurações para realizar disparos.'
        )

        return redirect('campanhas:aniversariantes_mes')

    
    if request.method == 'POST':
        form = DisparoAniversariantesForm(
            request.POST,
            matriz=contexto['matriz']
        )

        if form.is_valid():

            canais = []

            if form.cleaned_data['enviar_email']:
                canais.append(CampanhaAniversarioEnvio.CANAL_EMAIL)

            if form.cleaned_data['enviar_whatsapp']:
                canais.append(CampanhaAniversarioEnvio.CANAL_WHATSAPP)

            if form.cleaned_data['enviar_sms']:
                canais.append(CampanhaAniversarioEnvio.CANAL_SMS)

            total = registrar_disparos_aniversariantes(
                matriz=contexto['matriz'],
                clientes=clientes,
                canais=canais,
                assunto=form.cleaned_data['assunto'],
                mensagem=form.cleaned_data['mensagem'],
                template=form.cleaned_data.get('template'),
            )

            registrar_auditoria(
                usuario=request.user,
                matriz=contexto['matriz'],
                loja=contexto['loja'],
                acao=RegistroAuditoria.ACAO_DISPARAR,
                recurso='campanhas.aniversariantes',
                descricao=f'{total} envios de campanha de aniversário registrados.',
                request=request
            )

            messages.success(
                request,
                f'{total} envios foram registrados para disparo.'
            )

            return redirect('campanhas:aniversariantes_mes')

    else:
        form = DisparoAniversariantesForm(
            matriz=contexto['matriz'],
            initial={
                'assunto': configuracao.assunto_padrao,
                'mensagem': configuracao.mensagem_padrao,
                'enviar_email': configuracao.canal_padrao == CampanhaAniversarioEnvio.CANAL_EMAIL,
                'enviar_whatsapp': configuracao.canal_padrao == CampanhaAniversarioEnvio.CANAL_WHATSAPP,
                'enviar_sms': configuracao.canal_padrao == CampanhaAniversarioEnvio.CANAL_SMS,
            }
        )

    

    return render(
        request,
        'campanhas/disparar_aniversariantes.html',
        {
            'form': form,
            'total_clientes': clientes.count(),
            'configuracao': configuracao,
            'template_json_url': get_template_json_url_placeholder(),
            'template_json_placeholder': get_template_json_placeholder(),
        }
    )

@login_required
@require_permission(PERMISSAO_CAMPANHAS_DISPARAR)
def reenviar_aniversariante(request, cliente_id):

    contexto = get_contexto_operacional_usuario(request.user)

    cliente = get_object_or_404(
        Cliente,
        id=cliente_id,
        matriz=contexto['matriz'],
        ativo=True
    )
    configuracao = get_configuracao_campanha_aniversario(
        matriz=contexto['matriz']
    )

    if not configuracao.ativa:
        messages.warning(
            request,
            'A campanha de aniversário está desativada. Ative a campanha nas configurações para reenviar.'
        )

        return redirect('campanhas:aniversariantes_mes')
    
    ultimo_envio = (
        CampanhaAniversarioEnvio.objects
        .filter(
            matriz=contexto['matriz'],
            cliente=cliente
        )
        .order_by('-criado_em')
        .first()
    )

    canal = (
        ultimo_envio.canal
        if ultimo_envio
        else CampanhaAniversarioEnvio.CANAL_EMAIL
    )

    total = registrar_reenvio_aniversariante(
        matriz=contexto['matriz'],
        cliente=cliente,
        canais=[canal],
        assunto=configuracao.assunto_padrao,
        mensagem=configuracao.mensagem_padrao,
    )

    messages.success(
        request,
        f'{total} reenvio registrado para {cliente.nome}.'
    )

    return redirect('campanhas:aniversariantes_mes')


@login_required
@require_permission(PERMISSAO_CAMPANHAS_DISPARAR)
def historico_envios(request):

    contexto = get_contexto_operacional_usuario(request.user)

    envios = get_historico_envios_aniversario(
        matriz=contexto['matriz']
    )

    busca = request.GET.get('q', '').strip()
    canal = request.GET.get('canal', '').strip()
    status = request.GET.get('status', '').strip()

    if busca:
        clientes_filtrados = Cliente.objects.filter(
            matriz=contexto['matriz'],
            ativo=True
        )

        clientes_filtrados = aplicar_busca_clientes(
            clientes_filtrados,
            busca
        ).values('id')

        envios = envios.filter(
            cliente_id__in=clientes_filtrados
        )

    if canal:
        envios = envios.filter(
            canal=canal
        )

    if status:
        envios = envios.filter(
            status=status
        )

    paginator = Paginator(envios, 50)

    page = request.GET.get('page')

    envios = paginator.get_page(page)

    canais_formatados = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': canal == valor,
        }
        for valor, nome in CampanhaAniversarioEnvio.CANAL_CHOICES
    ]

    status_formatados = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': status == valor,
        }
        for valor, nome in CampanhaAniversarioEnvio.STATUS_CHOICES
    ]

    return render(
        request,
        'campanhas/historico_envios.html',
        {
            'envios': envios,
            'busca': busca,
            'canal': canal,
            'status': status,
            'canais': canais_formatados,
            'status_choices': status_formatados,
        }
    )


@login_required
@require_permission(PERMISSAO_CAMPANHAS_DISPARAR)
def fila_envios(request):

    contexto = get_contexto_operacional_usuario(request.user)

    envios = get_fila_envios_aniversario(
        matriz=contexto['matriz']
    )

    busca = request.GET.get('q', '').strip()
    canal = request.GET.get('canal', '').strip()
    status = request.GET.get('status', '').strip()

    if busca:
        clientes_filtrados = Cliente.objects.filter(
            matriz=contexto['matriz'],
            ativo=True
        )

        clientes_filtrados = aplicar_busca_clientes(
            clientes_filtrados,
            busca
        ).values('id')

        envios = envios.filter(
            cliente_id__in=clientes_filtrados
        )

    if canal:
        envios = envios.filter(canal=canal)

    if status:
        envios = envios.filter(status=status)

    canais_formatados = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': canal == valor,
        }
        for valor, nome in CampanhaAniversarioEnvio.CANAL_CHOICES
    ]

    status_formatados = [
        {
            'valor': valor,
            'nome': nome,
            'selecionado': status == valor,
        }
        for valor, nome in CampanhaAniversarioEnvio.STATUS_CHOICES
    ]

    paginator = Paginator(envios, 50)

    page = request.GET.get('page')

    envios = paginator.get_page(page)

    return render(
        request,
        'campanhas/fila_envios.html',
        {
            'envios': envios,
            'busca': busca,
            'canal': canal,
            'status': status,
            'canais': canais_formatados,
            'status_choices': status_formatados,
        }
    )

@login_required
@require_permission(PERMISSAO_CAMPANHAS_CONFIGURAR)
def configurar_campanha_aniversario(request):

    contexto = get_contexto_operacional_usuario(request.user)

    configuracao = get_configuracao_campanha_aniversario(
        matriz=contexto['matriz']
    )

    if request.method == 'POST':
        form = ConfiguracaoCampanhaAniversarioForm(
            request.POST,
            instance=configuracao
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Configuração da campanha atualizada com sucesso.'
            )

            return redirect('campanhas:configurar_campanha_aniversario')

    else:
        form = ConfiguracaoCampanhaAniversarioForm(
            instance=configuracao
        )

    return render(
        request,
        'campanhas/configurar_campanha_aniversario.html',
        {
            'form': form,
        }
    )


@login_required
@require_permission(PERMISSAO_CAMPANHAS_TEMPLATES)
def lista_templates_campanhas(request):

    contexto = get_contexto_operacional_usuario(request.user)

    templates = get_templates_campanhas(
        matriz=contexto['matriz']
    )

    return render(
        request,
        'campanhas/templates_campanhas.html',
        {
            'templates': templates,
        }
    )


@login_required
@require_permission(PERMISSAO_CAMPANHAS_TEMPLATES)
def criar_template_campanha(request):

    contexto = get_contexto_operacional_usuario(request.user)

    if request.method == 'POST':
        form = TemplateCampanhaForm(request.POST)

        if form.is_valid():
            template = form.save(commit=False)
            template.matriz = contexto['matriz']
            template.save()

            messages.success(
                request,
                'Template de campanha criado com sucesso.'
            )

            return redirect('campanhas:lista_templates_campanhas')

    else:
        form = TemplateCampanhaForm()

    
    preview = None

    if request.method == 'POST':
        assunto = request.POST.get('assunto', '')
        mensagem = request.POST.get('mensagem', '')
        contexto_preview = get_contexto_exemplo_template()

        preview = {
            'assunto': renderizar_mensagem_template(
                texto=assunto,
                contexto=contexto_preview
            ),
            'mensagem': renderizar_mensagem_template(
                texto=mensagem,
                contexto=contexto_preview
            ),
        }

    return render(
        request,
        'campanhas/form_template_campanha.html',
        {
            'form': form,
            'titulo': 'Novo Template de Campanha',
            'preview': preview,
        }
    )


@login_required
@require_permission(PERMISSAO_CAMPANHAS_TEMPLATES)
def editar_template_campanha(request, template_id):

    contexto = get_contexto_operacional_usuario(request.user)

    template = get_object_or_404(
        TemplateCampanha,
        id=template_id,
        matriz=contexto['matriz']
    )

    if request.method == 'POST':
        form = TemplateCampanhaForm(
            request.POST,
            instance=template
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Template de campanha atualizado com sucesso.'
            )

            return redirect('campanhas:lista_templates_campanhas')

    else:
        form = TemplateCampanhaForm(
            instance=template
        )

    return render(
        request,
        'campanhas/form_template_campanha.html',
        {
            'form': form,
            'titulo': 'Editar Template de Campanha',
            'template': template,
        }
    )


@login_required
@require_permission(PERMISSAO_CAMPANHAS_TEMPLATES)
def detalhe_template_campanha_json(request, template_id):

    contexto = get_contexto_operacional_usuario(request.user)

    template = get_object_or_404(
        TemplateCampanha,
        id=template_id,
        matriz=contexto['matriz'],
        ativo=True
    )

    return JsonResponse({
        'id': template.id,
        'nome': template.nome,
        'canal': template.canal,
        'assunto': template.assunto,
        'mensagem': template.mensagem,
    })