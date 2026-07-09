from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from cashback.services.compra import registrar_compra
from cashback.services.validacoes import (
    validar_limite_beneficios,
    validar_voucher_pre_venda,
)
from vouchers.services import registrar_uso_voucher


@transaction.atomic
def registrar_venda(
    *,
    matriz,
    loja,
    usuario,
    cpf,
    nome,
    valor_compra,
    valor_cashback_usado=0,
    aplicar_voucher=False,
    codigo_voucher='',
    telefone='',
    email='',
    data_nascimento=None,
    aceita_email=True,
    aceita_sms=False,
    observacao='',
):
    valor_compra = Decimal(valor_compra)
    valor_cashback_usado = Decimal(valor_cashback_usado or 0)

    voucher_validado = None
    desconto_voucher = Decimal('0.00')

    if aplicar_voucher:
        if not codigo_voucher:
            raise ValidationError(
                'Informe o código do voucher para aplicar o benefício.'
            )

        resultado_voucher = validar_voucher_pre_venda(
            matriz=matriz,
            loja=loja,
            codigo_voucher=codigo_voucher,
            valor_compra=valor_compra,
        )

        voucher_validado = resultado_voucher['voucher']
        desconto_voucher = resultado_voucher['desconto']

    validar_limite_beneficios(
        matriz=matriz,
        valor_compra=valor_compra,
        valor_cashback_usado=valor_cashback_usado,
        valor_desconto_voucher=desconto_voucher,
    )

    valor_base_cashback = valor_compra - desconto_voucher

    if valor_base_cashback < Decimal('0.00'):
        valor_base_cashback = Decimal('0.00')

    lancamento = registrar_compra(
        matriz=matriz,
        loja=loja,
        cpf=cpf,
        nome=nome,
        telefone=telefone,
        email=email,
        data_nascimento=data_nascimento,
        valor_compra=valor_compra,
        valor_base_cashback=valor_base_cashback,
        valor_cashback_usado=valor_cashback_usado,
        aceita_email=aceita_email,
        aceita_sms=aceita_sms,
        observacao=observacao,
    )

    uso_voucher = None

    if aplicar_voucher:
        uso_voucher = registrar_uso_voucher(
            matriz=matriz,
            loja=loja,
            cliente=lancamento.cliente,
            voucher=voucher_validado,
            usuario=usuario,
            compra=lancamento,
            valor_compra=valor_compra,
            valor_desconto=desconto_voucher,
            observacao='Uso de voucher na compra atual.',
        )

    return {
        'compra': lancamento,
        'cliente': lancamento.cliente,
        'uso_voucher': uso_voucher,
        'beneficios': {
            'cashback_usado': valor_cashback_usado,
            'voucher': voucher_validado,
            'desconto_voucher': desconto_voucher,
            'valor_base_cashback': valor_base_cashback,
        }
    }