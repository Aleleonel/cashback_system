from decimal import Decimal

from django.core.exceptions import ValidationError

from beneficios.selectors import get_voucher_por_codigo
from beneficios.services import calcular_desconto_voucher
from core.services import garantir_configuracao_sistema
from vouchers.services import validar_voucher


def calcular_limite_maximo_beneficios(
    *,
    matriz,
    valor_compra,
):
    configuracao = garantir_configuracao_sistema(
        matriz=matriz
    )

    valor_compra = Decimal(valor_compra)

    return (
        valor_compra *
        configuracao.percentual_maximo_beneficio /
        Decimal('100')
    ).quantize(Decimal('0.01'))


def validar_limite_beneficios(
    *,
    matriz,
    valor_compra,
    valor_cashback_usado=0,
    valor_desconto_voucher=0,
):
    valor_cashback_usado = Decimal(valor_cashback_usado or 0)
    valor_desconto_voucher = Decimal(valor_desconto_voucher or 0)

    if valor_cashback_usado > 0 and valor_desconto_voucher > 0:
        raise ValidationError(
            'Não é permitido usar cashback e voucher na mesma compra. Escolha apenas um benefício.'
        )

    total_beneficios = valor_cashback_usado + valor_desconto_voucher

    limite = calcular_limite_maximo_beneficios(
        matriz=matriz,
        valor_compra=valor_compra
    )

    if total_beneficios > limite:
        raise ValidationError(
            f'O total de benefícios não pode ultrapassar R$ {limite}.'
        )


def validar_voucher_pre_venda(
    *,
    matriz,
    loja,
    codigo_voucher,
    valor_compra,
):
    voucher = get_voucher_por_codigo(
        matriz=matriz,
        codigo=codigo_voucher
    )

    if voucher is None:
        raise ValidationError(
            'Voucher não encontrado.'
        )

    valido, mensagem = validar_voucher(
        voucher=voucher
    )

    if not valido:
        raise ValidationError(mensagem)

    lojas_permitidas = voucher.lojas_permitidas.all()

    if lojas_permitidas.exists():
        permitido = lojas_permitidas.filter(
            loja=loja
        ).exists()

        if not permitido:
            raise ValidationError(
                'Este voucher não é válido para esta loja.'
            )

    desconto = calcular_desconto_voucher(
        voucher=voucher,
        valor_compra=valor_compra
    )

    return {
        'voucher': voucher,
        'desconto': desconto,
    }