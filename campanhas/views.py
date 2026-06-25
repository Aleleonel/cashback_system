from django.shortcuts import get_object_or_404
from clientes.models import Cliente
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import models
from core.services import get_contexto_operacional_usuario
from clientes.selectors import aplicar_busca_clientes

from clientes.utils import limpar_numero, normalizar_texto

from .selectors import (
    get_aniversariantes_do_mes,
    get_historico_envios_aniversario,
    get_fila_envios_aniversario,
    get_configuracao_campanha_aniversario,
)

from django.contrib import messages
from django.shortcuts import redirect

from .forms import (
    DisparoAniversariantesForm, 
    ConfiguracaoCampanhaAniversarioForm,
)

from .models import CampanhaAniversarioEnvio
from .services import (
    registrar_disparos_aniversariantes, 
    registrar_reenvio_aniversariante,
    
)


@login_required
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
        form = DisparoAniversariantesForm(request.POST)

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
            )

            messages.success(
                request,
                f'{total} envios foram registrados para disparo.'
            )

            return redirect('campanhas:aniversariantes_mes')

    else:
        form = DisparoAniversariantesForm(
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
        }
    )

@login_required
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