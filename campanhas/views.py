from django.shortcuts import get_object_or_404
from clientes.models import Cliente

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import models
from core.services import get_contexto_operacional_usuario

from .selectors import (
    get_aniversariantes_do_mes,
    get_historico_envios_aniversario,
    get_fila_envios_aniversario,
)

from django.contrib import messages
from django.shortcuts import redirect

from .forms import DisparoAniversariantesForm
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

    busca = request.GET.get('q', '').strip()

    if busca:
        busca_numerica = ''.join(filter(str.isdigit, busca))

        if busca:
            busca_numerica = ''.join(filter(str.isdigit, busca))

            aniversariantes = aniversariantes.filter(
                models.Q(nome__icontains=busca) |
                models.Q(email__icontains=busca) |
                models.Q(cpf__icontains=busca) |
                models.Q(telefone__icontains=busca) |
                models.Q(cpf_normalizado__icontains=busca_numerica) |
                models.Q(telefone_normalizado__icontains=busca_numerica)
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
            
        }
    )

@login_required
def disparar_aniversariantes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    clientes = get_aniversariantes_do_mes(
        matriz=contexto['matriz']
    )

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
        form = DisparoAniversariantesForm()

    return render(
        request,
        'campanhas/disparar_aniversariantes.html',
        {
            'form': form,
            'total_clientes': clientes.count(),
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
        assunto='Feliz aniversário! Temos um presente especial para você',
        mensagem=(
            'Olá, {nome}! A equipe preparou uma condição especial '
            'para comemorar seu aniversário. Entre em contato e aproveite!'
        ),
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
        envios = envios.filter(
            models.Q(cliente__nome__icontains=busca) |
            models.Q(cliente__cpf__icontains=busca) |
            models.Q(cliente__cpf_normalizado__icontains=''.join(filter(str.isdigit, busca)))
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
        busca_numerica = ''.join(filter(str.isdigit, busca))

        envios = envios.filter(
            models.Q(cliente__nome__icontains=busca) |
            models.Q(cliente__cpf__icontains=busca) |
            models.Q(cliente__cpf_normalizado__icontains=busca_numerica)
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