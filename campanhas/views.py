from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import models
from core.services import get_contexto_operacional_usuario

from .selectors import get_aniversariantes_do_mes

from django.contrib import messages
from django.shortcuts import redirect

from .forms import DisparoAniversariantesForm
from .models import CampanhaAniversarioEnvio
from .services import registrar_disparos_aniversariantes

from django.db.models import F, Value
from django.db.models.functions import Replace

@login_required
def aniversariantes_mes(request):

    contexto = get_contexto_operacional_usuario(request.user)

    aniversariantes = get_aniversariantes_do_mes(
        matriz=contexto['matriz']
    )

    busca = request.GET.get('q', '').strip()

    if busca:
        busca_numerica = ''.join(filter(str.isdigit, busca))

        aniversariantes = aniversariantes.annotate(
            telefone_limpo=Replace(
                Replace(
                    Replace(
                        Replace(
                            Replace(
                                F('telefone'),
                                Value('('),
                                Value('')
                            ),
                            Value(')'),
                            Value('')
                        ),
                        Value(' '),
                        Value('')
                    ),
                    Value('-'),
                    Value('')
                ),
                Value('.'),
                Value('')
            ),
            cpf_limpo=Replace(
                Replace(
                    Replace(
                        F('cpf'),
                        Value('.'),
                        Value('')
                    ),
                    Value('-'),
                    Value('')
                ),
                Value(' '),
                Value('')
            )
        ).filter(
            models.Q(nome__icontains=busca) |
            models.Q(email__icontains=busca) |
            models.Q(cpf__icontains=busca) |
            models.Q(telefone__icontains=busca) |
            models.Q(cpf_limpo__icontains=busca_numerica) |
            models.Q(telefone_limpo__icontains=busca_numerica)
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