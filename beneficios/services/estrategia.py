from decimal import Decimal

from beneficios.selectors import get_vouchers_disponiveis


def calcular_desconto_voucher(*, voucher, valor_compra):
    valor_compra = Decimal(valor_compra)

    if voucher.tipo == voucher.Tipo.VALOR_FIXO:
        return min(voucher.valor, valor_compra)

    if voucher.tipo == voucher.Tipo.PERCENTUAL:
        desconto = valor_compra * voucher.percentual / Decimal('100')
        return desconto.quantize(Decimal('0.01'))

    return Decimal('0.00')


def get_melhor_voucher(*, matriz, cliente, valor_compra):
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


def selecionar_voucher_recomendado(*, matriz, cliente, valor_compra):
    vouchers = get_vouchers_disponiveis(
        matriz=matriz,
        cliente=cliente
    )

    if not vouchers:
        return None

    vouchers = sorted(
        vouchers,
        key=lambda voucher: (
            voucher.data_fim,
            -calcular_desconto_voucher(
                voucher=voucher,
                valor_compra=valor_compra
            ),
            voucher.criado_em,
        )
    )

    return vouchers[0]