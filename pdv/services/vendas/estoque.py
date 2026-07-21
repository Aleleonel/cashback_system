import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from estoque.models import ReservaEstoque
from estoque.services import (
    liberar_reserva_estoque,
    registrar_reserva_estoque,
)
from pdv.models import ItemVenda


def _origem_id_item(item):
    return str(item.uuid)


def _gerar_chave_reserva(item):
    atualizado = item.atualizado_em
    versao = (
        atualizado.strftime("%Y%m%d%H%M%S%f")
        if atualizado is not None
        else uuid.uuid4().hex
    )
    return f"pdv:item:{item.uuid}:reserva:{versao}"


def obter_reserva_ativa_item(*, item):
    return (
        ReservaEstoque.objects
        .filter(
            matriz=item.venda.matriz,
            loja=item.venda.loja,
            produto=item.produto,
            origem=OrigemMovimentacao.VENDA,
            origem_id=_origem_id_item(item),
            status=StatusReservaEstoque.ATIVA,
        )
        .order_by("-criada_em")
        .first()
    )


@transaction.atomic
def reservar_estoque_item(
    *,
    item,
    usuario=None,
    expira_em=None,
    request=None,
):
    item = (
        ItemVenda.objects
        .select_for_update()
        .select_related("venda", "produto")
        .get(pk=item.pk)
    )

    if item.cancelado:
        raise ValidationError({
            "item": "Nao e permitido reservar estoque para item cancelado."
        })

    if item.venda.status in {"finalizada", "cancelada"}:
        raise ValidationError({
            "venda": "Nao e permitido reservar estoque para venda encerrada."
        })

    if not item.produto.controla_estoque:
        return None

    reserva_atual = obter_reserva_ativa_item(item=item)

    if (
        reserva_atual is not None
        and reserva_atual.quantidade == item.quantidade
    ):
        return reserva_atual

    if reserva_atual is not None:
        liberar_reserva_estoque(
            reserva=reserva_atual,
            usuario=usuario,
            request=request,
        )

    resultado = registrar_reserva_estoque(
        matriz=item.venda.matriz,
        loja=item.venda.loja,
        produto=item.produto,
        origem=OrigemMovimentacao.VENDA,
        quantidade=Decimal(item.quantidade),
        chave_idempotencia=_gerar_chave_reserva(item),
        usuario=usuario,
        documento_referencia=str(item.venda.uuid),
        origem_id=_origem_id_item(item),
        expira_em=expira_em,
        request=request,
    )
    return resultado.reserva


@transaction.atomic
def liberar_reserva_item(
    *,
    item,
    usuario=None,
    request=None,
):
    item = (
        ItemVenda.objects
        .select_for_update()
        .select_related("venda", "produto")
        .get(pk=item.pk)
    )

    if not item.produto.controla_estoque:
        return None

    reserva = obter_reserva_ativa_item(item=item)
    if reserva is None:
        return None

    resultado = liberar_reserva_estoque(
        reserva=reserva,
        usuario=usuario,
        request=request,
    )
    return resultado.reserva
