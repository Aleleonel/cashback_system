from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from estoque.choices import (
    OrigemMovimentacao,
    StatusReservaEstoque,
    TipoMovimentacao,
)
from estoque.models import ReservaEstoque

from .resultados import ResultadoConfirmacaoReservaEstoque
from .saidas import registrar_saida_estoque


@transaction.atomic
def confirmar_reserva_estoque(
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

    if reserva_bloqueada.origem != OrigemMovimentacao.VENDA:
        raise ValidationError({
            'origem': (
                'Somente reservas originadas por venda '
                'podem ser confirmadas.'
            )
        })

    chave_movimentacao = _gerar_chave_movimentacao(
        reserva=reserva_bloqueada
    )

    if reserva_bloqueada.status == StatusReservaEstoque.CONFIRMADA:
        resultado_saida = registrar_saida_estoque(
            matriz=reserva_bloqueada.matriz,
            loja=reserva_bloqueada.loja,
            produto=reserva_bloqueada.produto,
            tipo=TipoMovimentacao.VENDA,
            origem=OrigemMovimentacao.VENDA,
            quantidade=reserva_bloqueada.quantidade,
            chave_idempotencia=chave_movimentacao,
            usuario=usuario,
            observacao=_gerar_observacao(
                reserva=reserva_bloqueada
            ),
            documento_referencia=(
                reserva_bloqueada.documento_referencia
            ),
            origem_id=reserva_bloqueada.origem_id,
            request=request,
        )

        return ResultadoConfirmacaoReservaEstoque(
            reserva=reserva_bloqueada,
            saldo=resultado_saida.saldo,
            movimentacao=resultado_saida.movimentacao,
            duplicada=True,
        )

    if reserva_bloqueada.status != StatusReservaEstoque.ATIVA:
        raise ValidationError({
            'status': (
                'Somente uma reserva ativa pode ser confirmada.'
            )
        })

    resultado_saida = registrar_saida_estoque(
        matriz=reserva_bloqueada.matriz,
        loja=reserva_bloqueada.loja,
        produto=reserva_bloqueada.produto,
        tipo=TipoMovimentacao.VENDA,
        origem=OrigemMovimentacao.VENDA,
        quantidade=reserva_bloqueada.quantidade,
        chave_idempotencia=chave_movimentacao,
        usuario=usuario,
        observacao=_gerar_observacao(
            reserva=reserva_bloqueada
        ),
        documento_referencia=(
            reserva_bloqueada.documento_referencia
        ),
        origem_id=reserva_bloqueada.origem_id,
        request=request,
    )

    reserva_bloqueada.status = StatusReservaEstoque.CONFIRMADA
    reserva_bloqueada.confirmada_em = timezone.now()
    reserva_bloqueada.save(
        update_fields=[
            'status',
            'confirmada_em',
            'atualizado_em',
        ]
    )

    _registrar_auditoria_confirmacao(
        reserva=reserva_bloqueada,
        movimentacao=resultado_saida.movimentacao,
        usuario=usuario,
        request=request,
    )

    return ResultadoConfirmacaoReservaEstoque(
        reserva=reserva_bloqueada,
        saldo=resultado_saida.saldo,
        movimentacao=resultado_saida.movimentacao,
        duplicada=False,
    )


def _gerar_chave_movimentacao(*, reserva):
    return (
        f'{reserva.chave_idempotencia}:confirmacao'
    )


def _gerar_observacao(*, reserva):
    return (
        f'Consumo da reserva de estoque {reserva.uuid}.'
    )


def _registrar_auditoria_confirmacao(
    *,
    reserva,
    movimentacao,
    usuario,
    request,
):
    registrar_auditoria(
        usuario=usuario,
        matriz=reserva.matriz,
        loja=reserva.loja,
        acao=RegistroAuditoria.ACAO_EDITAR,
        recurso='estoque.reserva',
        recurso_id=reserva.uuid,
        descricao=(
            f'Confirmação de reserva de estoque: '
            f'produto={reserva.produto.codigo_interno}; '
            f'quantidade={reserva.quantidade}; '
            f'movimentacao={movimentacao.uuid}; '
            f'saldo_anterior={movimentacao.saldo_anterior}; '
            f'saldo_posterior={movimentacao.saldo_posterior}.'
        ),
        request=request,
    )
