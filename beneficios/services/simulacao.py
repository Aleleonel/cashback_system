from decimal import Decimal

from beneficios.selectors import get_cashback_disponivel

from .estrategia import (
    calcular_desconto_voucher,
    selecionar_voucher_recomendado,
)


def calcular_cashback_sugerido(*, matriz, cliente, valor_restante):
    saldo = get_cashback_disponivel(
        matriz=matriz,
        cliente=cliente
    )

    return min(
        saldo,
        valor_restante
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

    total_desconto = desconto_voucher + valor_cashback_usado

    if total_desconto > valor_compra:
        total_desconto = valor_compra

    valor_final = valor_compra - total_desconto

    return {
        'valor_compra': valor_compra,
        'desconto_voucher': desconto_voucher,
        'cashback_usado': valor_cashback_usado,
        'total_desconto': total_desconto,
        'valor_final': valor_final,
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

    valor_restante = valor_compra - desconto_voucher

    cashback_sugerido = calcular_cashback_sugerido(
        matriz=matriz,
        cliente=cliente,
        valor_restante=valor_restante
    )

    total_desconto = desconto_voucher + cashback_sugerido

    if total_desconto > valor_compra:
        total_desconto = valor_compra

    valor_final = valor_compra - total_desconto

    return {
        'valor_compra': valor_compra,
        'cashback_disponivel': cashback_disponivel,
        'voucher_sugerido': voucher_sugerido,
        'desconto_voucher': desconto_voucher,
        'cashback_sugerido': cashback_sugerido,
        'total_desconto': total_desconto,
        'valor_final': valor_final,
    }