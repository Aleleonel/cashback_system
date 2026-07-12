from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_CASHBACK_NOVA_COMPRA
from clientes.models import Cliente
from core.services import get_contexto_operacional_usuario

from beneficios.services import simular_beneficios


@login_required
@require_permission(PERMISSAO_CASHBACK_NOVA_COMPRA)
def simular_beneficios_view(request):

    try:
        contexto = get_contexto_operacional_usuario(request.user)

        cpf = ''.join(filter(str.isdigit, request.GET.get('cpf', '')))
        valor = request.GET.get('valor_compra', '0')

        if len(cpf) != 11:
            return JsonResponse({
                'ok': False,
                'erro': 'CPF inválido.'
            })

        try:
            valor = Decimal(valor)
        except Exception:
            valor = Decimal('0.00')

        cliente = Cliente.objects.filter(
            matriz=contexto['matriz'],
            cpf=cpf,
            ativo=True
        ).first()

        if not cliente:
            return JsonResponse({
                'ok': False,
                'erro': 'Cliente não encontrado.'
            })

        simulacao = simular_beneficios(
            matriz=contexto['matriz'],
            cliente=cliente,
            valor_compra=valor
        )

        voucher = simulacao['voucher_sugerido']

        return JsonResponse({
            'ok': True,

            'cashback_disponivel': float(
                simulacao['cashback_disponivel']
            ),

            'voucher': {
                'id': voucher.id,
                'nome': voucher.nome,
            } if voucher else None,

            'desconto_voucher': float(
                simulacao['desconto_voucher']
            ),

            'cashback_sugerido': float(
                simulacao['cashback_sugerido']
            ),

            'valor_final_cashback': float(
                simulacao['valor_final_cashback']
            ),

            'valor_final_voucher': float(
                simulacao['valor_final_voucher']
            ),
        })

    except ValidationError as erro:
        return JsonResponse({
            'ok': False,
            'erro': erro.message
        })