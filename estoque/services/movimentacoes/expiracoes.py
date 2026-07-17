from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from estoque.choices import StatusReservaEstoque
from estoque.models import ReservaEstoque
from estoque.selectors import get_saldo_disponivel

from .resultados import ResultadoReservaEstoque


@transaction.atomic
def expirar_reserva_estoque(
    *,
    reserva,
    usuario=None,
    request=None,
    agora=None,
):
    agora = agora or timezone.now()

    reserva_bloqueada = (
        ReservaEstoque.objects
        .select_for_update()
        .select_related(
            'matriz',
            'loja',
            'produto',
        )
        .get(pk=reserva.pk)
    )

    if reserva_bloqueada.status == StatusReservaEstoque.EXPIRADA:
        return ResultadoReservaEstoque(
            reserva=reserva_bloqueada,
            duplicada=True,
        )

    if reserva_bloqueada.status != StatusReservaEstoque.ATIVA:
        raise ValidationError({
            'status': (
                'Somente uma reserva ativa pode ser expirada.'
            )
        })

    if reserva_bloqueada.expira_em is None:
        raise ValidationError({
            'expira_em': (
                'A reserva não possui data de expiração.'
            )
        })

    if reserva_bloqueada.expira_em > agora:
        raise ValidationError({
            'expira_em': (
                'A reserva ainda não atingiu a data de expiração.'
            )
        })

    saldo_disponivel_anterior = get_saldo_disponivel(
        matriz=reserva_bloqueada.matriz,
        loja=reserva_bloqueada.loja,
        produto=reserva_bloqueada.produto,
    )

    reserva_bloqueada.status = StatusReservaEstoque.EXPIRADA
    reserva_bloqueada.expirada_em = agora
    reserva_bloqueada.save(
        update_fields=[
            'status',
            'expirada_em',
            'atualizado_em',
        ]
    )

    _registrar_auditoria_expiracao(
        reserva=reserva_bloqueada,
        usuario=usuario,
        saldo_disponivel_anterior=saldo_disponivel_anterior,
        request=request,
    )

    return ResultadoReservaEstoque(
        reserva=reserva_bloqueada,
        duplicada=False,
    )


def _registrar_auditoria_expiracao(
    *,
    reserva,
    usuario,
    saldo_disponivel_anterior,
    request,
):
    saldo_disponivel_posterior = (
        saldo_disponivel_anterior + reserva.quantidade
    )

    registrar_auditoria(
        usuario=usuario,
        matriz=reserva.matriz,
        loja=reserva.loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='estoque.reserva',
        recurso_id=reserva.uuid,
        descricao=(
            f'Expiração de reserva de estoque: '
            f'produto={reserva.produto.codigo_interno}; '
            f'quantidade={reserva.quantidade}; '
            f'expira_em={reserva.expira_em}; '
            f'expirada_em={reserva.expirada_em}; '
            f'saldo_disponivel_anterior={saldo_disponivel_anterior}; '
            f'saldo_disponivel_posterior={saldo_disponivel_posterior}.'
        ),
        request=request,
    )
