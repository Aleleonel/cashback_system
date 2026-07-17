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
def liberar_reserva_estoque(
    *,
    reserva,
    usuario=None,
    request=None,
):
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

    if reserva_bloqueada.status == StatusReservaEstoque.LIBERADA:
        return ResultadoReservaEstoque(
            reserva=reserva_bloqueada,
            duplicada=True,
        )

    if reserva_bloqueada.status != StatusReservaEstoque.ATIVA:
        raise ValidationError({
            'status': 'Somente uma reserva ativa pode ser liberada.'
        })

    saldo_disponivel_anterior = get_saldo_disponivel(
        matriz=reserva_bloqueada.matriz,
        loja=reserva_bloqueada.loja,
        produto=reserva_bloqueada.produto,
    )

    reserva_bloqueada.status = StatusReservaEstoque.LIBERADA
    reserva_bloqueada.liberada_em = timezone.now()
    reserva_bloqueada.save(
        update_fields=[
            'status',
            'liberada_em',
            'atualizado_em',
        ]
    )

    _registrar_auditoria_liberacao(
        reserva=reserva_bloqueada,
        usuario=usuario,
        saldo_disponivel_anterior=saldo_disponivel_anterior,
        request=request,
    )

    return ResultadoReservaEstoque(
        reserva=reserva_bloqueada,
        duplicada=False,
    )


def _registrar_auditoria_liberacao(
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
            f'LiberaÃ§Ã£o de reserva de estoque: '
            f'produto={reserva.produto.codigo_interno}; '
            f'quantidade={reserva.quantidade}; '
            f'saldo_disponivel_anterior={saldo_disponivel_anterior}; '
            f'saldo_disponivel_posterior={saldo_disponivel_posterior}.'
        ),
        request=request,
    )
