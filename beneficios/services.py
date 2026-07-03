from decimal import Decimal

from .selectors import get_cashback_disponivel, get_vouchers_disponiveis


def calcular_desconto_voucher(
    *,
    voucher,
    valor_compra,
):

    valor_compra = Decimal(valor_compra)

    if voucher.tipo == voucher.Tipo.VALOR_FIXO:
        return min(voucher.valor, valor_compra)

    if voucher.tipo == voucher.Tipo.PERCENTUAL:
        desconto = valor_compra * voucher.percentual / Decimal('100')
        return desconto.quantize(Decimal('0.01'))

    return Decimal('0.00')


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


def get_melhor_voucher(
    *,
    matriz,
    cliente,
    valor_compra,
):

    vouchers = get_vouchers_disponiveis(
        matriz=matriz,
        cliente=cliente
    )

    melhor_voucher = None
    maior_desconto = Decimal('0.00')

    for voucher in vouchers:
        desconto = calcular_desconto_voucher(
            voucher=voucher,
            valor_compra=valor_compra
        )

        if desconto > maior_desconto:
            maior_desconto = desconto
            melhor_voucher = voucher

    return melhor_voucher