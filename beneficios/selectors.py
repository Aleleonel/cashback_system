from decimal import Decimal

from cashback.selectors import get_saldo_disponivel_cliente
from vouchers.selectors import get_vouchers_cliente
from vouchers.services import validar_voucher
from vouchers.models import Voucher


def get_cashback_disponivel(
    *,
    matriz,
    cliente,
):

    return get_saldo_disponivel_cliente(
        matriz=matriz,
        cliente=cliente
    )


def get_vouchers_disponiveis(
    *,
    matriz,
    cliente,
):

    vouchers = get_vouchers_cliente(
        matriz=matriz,
        cliente=cliente
    )

    disponiveis = []

    for voucher in vouchers:
        valido, mensagem = validar_voucher(
            voucher=voucher
        )

        if valido:
            disponiveis.append(voucher)

    return disponiveis


def get_resumo_beneficios(
    *,
    matriz,
    cliente,
):

    cashback = get_cashback_disponivel(
        matriz=matriz,
        cliente=cliente
    )

    vouchers = get_vouchers_disponiveis(
        matriz=matriz,
        cliente=cliente
    )

    total_vouchers = Decimal('0.00')

    for voucher in vouchers:
        if voucher.tipo == voucher.Tipo.VALOR_FIXO and voucher.valor:
            total_vouchers += voucher.valor

    return {
        'cashback_disponivel': cashback,
        'vouchers_disponiveis': vouchers,
        'total_vouchers_valor_fixo': total_vouchers,
        'total_beneficios_estimado': cashback + total_vouchers,
    }

def get_voucher_por_codigo(
    *,
    matriz,
    codigo,
):
    """
    Localiza um voucher pelo código dentro da matriz.
    """

    return (
        Voucher.objects
        .filter(
            matriz=matriz,
            codigo=codigo.strip().upper(),
        )
        .first()
    )