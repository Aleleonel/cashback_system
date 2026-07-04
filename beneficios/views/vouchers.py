from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_CASHBACK_NOVA_COMPRA
from clientes.models import Cliente
from core.services import get_contexto_operacional_usuario

from beneficios.services import validar_voucher_para_compra


@login_required
@require_permission(PERMISSAO_CASHBACK_NOVA_COMPRA)
def validar_voucher_view(request):

    contexto = get_contexto_operacional_usuario(request.user)

    cpf = ''.join(filter(str.isdigit, request.GET.get('cpf', '')))
    codigo = request.GET.get('codigo', '').strip()

    try:
        valor_compra = Decimal(
            request.GET.get('valor_compra', '0')
        )
    except InvalidOperation:
        valor_compra = Decimal('0.00')

    if len(cpf) != 11:
        return JsonResponse({
            'ok': False,
            'mensagem': 'CPF inválido.'
        })

    if not codigo:
        return JsonResponse({
            'ok': False,
            'mensagem': 'Informe o código do voucher.'
        })

    cliente = Cliente.objects.filter(
        matriz=contexto['matriz'],
        cpf=cpf,
        ativo=True
    ).first()

    if cliente is None:
        return JsonResponse({
            'ok': False,
            'mensagem': 'Cliente não encontrado.'
        })

    resultado = validar_voucher_para_compra(
        matriz=contexto['matriz'],
        loja=contexto['loja'],
        cliente=cliente,
        codigo=codigo,
        valor_compra=valor_compra
    )


    if not resultado['ok']:
        return JsonResponse(resultado)

    voucher = resultado['voucher']

    return JsonResponse({
        'ok': True,
        'id': voucher.id,
        'codigo': voucher.codigo,
        'nome': voucher.nome,
        'tipo': voucher.get_tipo_display(),
        'desconto': float(resultado['desconto']),
        'mensagem': resultado['mensagem'],
    })