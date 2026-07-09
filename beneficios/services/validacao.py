from beneficios.selectors import get_voucher_por_codigo
from vouchers.services import validar_voucher

from .estrategia import calcular_desconto_voucher


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