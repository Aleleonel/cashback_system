from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.services import get_contexto_operacional_usuario

from .selectors import get_cliente_por_cpf


@login_required
def buscar_cliente_cpf(request):

    cpf = request.GET.get('cpf')

    if not cpf:
        return JsonResponse({
            'encontrado': False
        })

    contexto = get_contexto_operacional_usuario(
        request.user
    )

    cliente = get_cliente_por_cpf(
        contexto['matriz'],
        cpf
    )

    if not cliente:
        return JsonResponse({
            'encontrado': False
        })

    return JsonResponse({
        'encontrado': True,
        'nome': cliente.nome,
        'telefone': cliente.telefone,
        'email': cliente.email,
    })