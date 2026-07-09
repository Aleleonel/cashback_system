from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from vouchers.models import Voucher


@transaction.atomic
def ativar_voucher(*, voucher, usuario_executor, request=None):

    voucher.status = Voucher.Status.ATIVO
    voucher.save(update_fields=['status'])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=voucher.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher ativado: {voucher.codigo}',
        request=request,
    )


@transaction.atomic
def inativar_voucher(*, voucher, usuario_executor, request=None):

    voucher.status = Voucher.Status.INATIVO
    voucher.save(update_fields=['status'])

    registrar_auditoria(
        usuario=usuario_executor,
        matriz=voucher.matriz,
        loja=None,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='voucher',
        recurso_id=voucher.id,
        descricao=f'Voucher inativado: {voucher.codigo}',
        request=request,
    )