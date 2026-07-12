from decimal import Decimal

from django.core.exceptions import ValidationError

from beneficios.selectors import get_cashback_disponivel

from .estrategia import (
    calcular_desconto_voucher,
    selecionar_voucher_recomendado,
)

def calcular_cashback_sugerido(*, matriz, cliente, valor_compra):
    from cashback.services.validacoes import (
        calcular_limite_maximo_beneficios,
    )

    saldo = get_cashback_disponivel(
        matriz=matriz,
        cliente=cliente
    )

    limite = calcular_limite_maximo_beneficios(
        matriz=matriz,
        valor_compra=valor_compra
    )

    return min(
        saldo,
        limite
    )

def simular_compra(
    *,
    matriz,
    cliente,
    valor_compra,
    voucher=None,
    valor_cashback_usado=0,
):
    valor_compra = Decimal(valor_compra)
    valor_cashback_usado = Decimal(valor_cashback_usado or 0)

    cashback_disponivel = get_cashback_disponivel(
        matriz=matriz,
        cliente=cliente
    )

    if valor_cashback_usado > cashback_disponivel:
        valor_cashback_usado = cashback_disponivel

    desconto_voucher = Decimal('0.00')

    if voucher:
        desconto_voucher = calcular_desconto_voucher(
            voucher=voucher,
            valor_compra=valor_compra
        )

    if voucher and valor_cashback_usado > Decimal('0.00'):
        raise ValidationError(
            'Cashback e voucher não podem ser simulados juntos.'
        )

    if voucher:
        total_desconto = min(
            desconto_voucher,
            valor_compra
        )
        beneficio_aplicado = 'VOUCHER'
    else:
        total_desconto = min(
            valor_cashback_usado,
            valor_compra
        )
        beneficio_aplicado = (
            'CASHBACK'
            if valor_cashback_usado > Decimal('0.00')
            else 'NENHUM'
        )

    valor_final = valor_compra - total_desconto

    return {
        'valor_compra': valor_compra,
        'desconto_voucher': desconto_voucher,
        'cashback_usado': valor_cashback_usado,
        'total_desconto': total_desconto,
        'valor_final': valor_final,
        'beneficio_aplicado': beneficio_aplicado,
    }


def simular_beneficios(*, matriz, cliente, valor_compra):
    valor_compra = Decimal(valor_compra)

    cashback_disponivel = get_cashback_disponivel(
        matriz=matriz,
        cliente=cliente
    )

    voucher_sugerido = selecionar_voucher_recomendado(
        matriz=matriz,
        cliente=cliente,
        valor_compra=valor_compra
    )

    desconto_voucher = Decimal('0.00')

    if voucher_sugerido:
        desconto_voucher = calcular_desconto_voucher(
            voucher=voucher_sugerido,
            valor_compra=valor_compra
        )

    cashback_sugerido = calcular_cashback_sugerido(
        matriz=matriz,
        cliente=cliente,
        valor_compra=valor_compra
    )

    valor_final_cashback = (
        valor_compra
        - min(cashback_sugerido, valor_compra)
    )

    valor_final_voucher = (
        valor_compra
        - min(desconto_voucher, valor_compra)
    )

    return {
        'valor_compra': valor_compra,
        'cashback_disponivel': cashback_disponivel,
        'voucher_sugerido': voucher_sugerido,
        'desconto_voucher': desconto_voucher,
        'cashback_sugerido': cashback_sugerido,
        'valor_final_cashback': valor_final_cashback,
        'valor_final_voucher': valor_final_voucher,
    }
