from django.core.exceptions import ValidationError
from django.db import transaction

from cashback.services.compra import registrar_compra
from beneficios.services import validar_voucher_para_compra
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
    lancamento = registrar_compra(
        matriz=matriz,
        loja=loja,
        cpf=cpf,
        nome=nome,
        telefone=telefone,
        email=email,
        data_nascimento=data_nascimento,
        valor_compra=valor_compra,
        valor_cashback_usado=valor_cashback_usado,
        aceita_email=aceita_email,
        aceita_sms=aceita_sms,
        observacao=observacao,
    )

    uso_voucher = None

    if aplicar_voucher:
        if not codigo_voucher:
            raise ValidationError(
                'Informe o código do voucher para aplicar o benefício.'
            )

        resultado = validar_voucher_para_compra(
            matriz=matriz,
            loja=loja,
            cliente=lancamento.cliente,
            codigo=codigo_voucher,
            valor_compra=valor_compra,
        )

        if not resultado['ok']:
            raise ValidationError(resultado['mensagem'])

        uso_voucher = registrar_uso_voucher(
            matriz=matriz,
            loja=loja,
            cliente=lancamento.cliente,
            voucher=resultado['voucher'],
            usuario=usuario,
            compra=lancamento,
            valor_compra=valor_compra,
            valor_desconto=resultado['desconto'],
            observacao='Uso de voucher na compra atual.',
        )

    return {
        'lancamento': lancamento,
        'uso_voucher': uso_voucher,
    }