from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from vouchers.models import Voucher, UsoVoucher
from .validacao import validar_voucher


def utilizar_voucher():
    raise NotImplementedError()


def cancelar_utilizacao():
    raise NotImplementedError()


@transaction.atomic
def registrar_uso_voucher(
    *,
    matriz,
    loja,
    cliente,
    voucher,
    usuario,
    compra,
    valor_compra,
    valor_desconto,
    observacao='',
):
    voucher_bloqueado = Voucher.objects.select_for_update().get(
        id=voucher.id,
        matriz=matriz
    )

    valido, mensagem = validar_voucher(voucher=voucher_bloqueado)

    if not valido:
        raise ValidationError(mensagem)

    if voucher_bloqueado.total_utilizado >= voucher_bloqueado.limite_utilizacao:
        raise ValidationError('Voucher sem utilizações disponíveis.')

    lojas_permitidas = voucher_bloqueado.lojas_permitidas.all()

    if lojas_permitidas.exists():
        permitido = lojas_permitidas.filter(loja=loja).exists()

        if not permitido:
            raise ValidationError('Este voucher não é válido para esta loja.')

    uso = UsoVoucher.objects.create(
        matriz=matriz,
        loja=loja,
        cliente=cliente,
        voucher=voucher_bloqueado,
        usuario=usuario,
        compra=compra,
        valor_compra=valor_compra,
        valor_desconto=valor_desconto,
        observacao=observacao,
    )

    Voucher.objects.filter(
        id=voucher_bloqueado.id,
        total_utilizado__lt=F('limite_utilizacao')
    ).update(
        total_utilizado=F('total_utilizado') + 1
    )

    return uso