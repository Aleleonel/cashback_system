from decimal import Decimal

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from accounts.decorators import require_permission
from accounts.permissions import PERMISSAO_CASHBACK_NOVA_COMPRA

from clientes.models import Cliente
from core.services import get_contexto_operacional_usuario

from .services import (
    simular_beneficios, 
    validar_voucher_para_compra,
)

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

        voucher = simulacao['voucher_recomendado']

        return JsonResponse({

            'ok': True,

            'cashback_disponivel': float(simulacao['cashback_disponivel']),

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

            'total_desconto': float(
                simulacao['total_desconto']
            ),

            'valor_final': float(
                simulacao['valor_final']
            )

        })

    except ValidationError as erro:

        return JsonResponse({
            'ok': False,
            'erro': erro.message
        })
    

@login_required
@require_permission(PERMISSAO_CASHBACK_NOVA_COMPRA)
def validar_voucher_view(request):

    contexto = get_contexto_operacional_usuario(
        request.user
    )

    cpf = ''.join(
        filter(
            str.isdigit,
            request.GET.get("cpf", "")
        )
    )

    codigo = request.GET.get(
        "codigo",
        ""
    ).strip()

    valor = Decimal(
        request.GET.get(
            "valor_compra",
            "0"
        )
    )

    cliente = Cliente.objects.filter(
        matriz=contexto["matriz"],
        cpf=cpf,
        ativo=True,
    ).first()

    if cliente is None:

        return JsonResponse({

            "ok": False,

            "mensagem": "Cliente não encontrado."

        })

    resultado = validar_voucher_para_compra(

        matriz=contexto["matriz"],

        cliente=cliente,

        codigo=codigo,

        valor_compra=valor,

    )

    if not resultado["ok"]:

        return JsonResponse(resultado)

    voucher = resultado["voucher"]

    return JsonResponse({

        "ok": True,

        "nome": voucher.nome,

        "tipo": voucher.get_tipo_display(),

        "desconto": float(
            resultado["desconto"]
        ),

        "mensagem": resultado["mensagem"],

    })