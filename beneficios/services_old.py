from decimal import Decimal

from .selectors import (
    get_cashback_disponivel,
    get_vouchers_disponiveis,
    get_voucher_por_codigo,
)

from vouchers.services import validar_voucher

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


def selecionar_voucher_recomendado(
    *,
    matriz,
    cliente,
    valor_compra,
):
    """
    Seleciona o voucher recomendado conforme a política do sistema.

    Ordem atual:

    1 - Voucher que vence primeiro.
    2 - Maior desconto.
    3 - Voucher mais antigo.

    Esta política poderá ser configurável futuramente.
    """

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

def simular_beneficios(
    *,
    matriz,
    cliente,
    valor_compra,
):

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

def calcular_cashback_sugerido(
    *,
    matriz,
    cliente,
    valor_restante,
):
    """
    Sugere quanto de cashback utilizar.

    A sugestão nunca ultrapassa:

    - saldo disponível
    - valor restante da compra
    """

    saldo = get_cashback_disponivel(
        matriz=matriz,
        cliente=cliente
    )

    return min(
        saldo,
        valor_restante
    )

def validar_voucher_para_compra(
    *,
    matriz,
    loja,
    cliente,
    codigo,
    valor_compra,
):
    voucher = get_voucher_por_codigo(
        matriz=matriz,
        codigo=codigo,
    )

    if voucher is None:
        return {
            'ok': False,
            'mensagem': 'Voucher não encontrado.'
        }

    valido, mensagem = validar_voucher(
        voucher=voucher
    )

    if not valido:
        return {
            'ok': False,
            'mensagem': mensagem,
        }

    

    lojas_permitidas = voucher.lojas_permitidas.all()

    if lojas_permitidas.exists():
        permitido = lojas_permitidas.filter(
            loja=loja
        ).exists()

        if not permitido:
            return {
                'ok': False,
                'mensagem': 'Este voucher não é válido para esta loja.'
            }

    desconto = calcular_desconto_voucher(
        voucher=voucher,
        valor_compra=valor_compra,
    )

    return {
        'ok': True,
        'voucher': voucher,
        'desconto': desconto,
        'mensagem': 'Voucher válido.'
    }