from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from core.services import get_contexto_operacional_usuario
from cashback.selectors import get_saldo_disponivel_cliente

from .selectors import get_cliente_por_cpf


@login_required
def buscar_cliente_cpf(request):

    cpf = request.GET.get('cpf')

    if not cpf:
        return JsonResponse({
            'encontrado': False
        })

    try:
        contexto = get_contexto_operacional_usuario(request.user)

    except ValidationError as erro:
        return JsonResponse({
            'encontrado': False,
            'erro': erro.message
        }, status=400)

    cliente = get_cliente_por_cpf(
        matriz=contexto['matriz'],
        cpf=cpf
    )

    if not cliente:
        return JsonResponse({
            'encontrado': False
        })

    saldo_disponivel = get_saldo_disponivel_cliente(
        matriz=contexto['matriz'],
        cliente=cliente
    )

    return JsonResponse({
        'encontrado': True,
        'nome': cliente.nome,
        'telefone': cliente.telefone or '',
        'email': cliente.email or '',
        'saldo_disponivel': str(saldo_disponivel),
        'data_nascimento': (
            cliente.data_nascimento.strftime('%d/%m/%Y')
            if cliente.data_nascimento
            else ''
        )
    })