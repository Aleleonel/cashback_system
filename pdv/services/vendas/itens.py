from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from pdv.models import ItemVenda, Venda


def _decimal(valor, *, campo, casas):
    try:
        resultado = Decimal(str(valor))
        if not resultado.is_finite():
            raise InvalidOperation
        return resultado.quantize(Decimal(casas))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({campo: f"Informe um valor valido para {campo}."})


def _validar_venda_editavel(venda):
    if venda.status in {"finalizada", "cancelada"}:
        raise ValidationError({"venda": "Nao e permitido alterar uma venda encerrada."})


@transaction.atomic
def adicionar_item_venda(
    *,
    venda,
    produto,
    quantidade=Decimal("1.000"),
    preco_unitario=None,
    desconto=Decimal("0.00"),
    acrescimo=Decimal("0.00"),
    observacao="",
    reservar_estoque=True,
    usuario=None,
    expira_em=None,
    request=None,
):
    venda = Venda.objects.select_for_update().get(pk=venda.pk)
    _validar_venda_editavel(venda)
    if produto.matriz_id != venda.matriz_id:
        raise ValidationError({"produto": "O produto deve pertencer a mesma matriz da venda."})
    if preco_unitario is None:
        preco_unitario = produto.preco_venda
    ultima = ItemVenda.objects.filter(venda=venda).aggregate(valor=Max("sequencia")).get("valor") or 0
    item = ItemVenda(
        venda=venda,
        produto=produto,
        sequencia=ultima + 1,
        quantidade=_decimal(quantidade, campo="quantidade", casas="0.001"),
        preco_unitario=_decimal(preco_unitario, campo="preco_unitario", casas="0.01"),
        desconto=_decimal(desconto, campo="desconto", casas="0.01"),
        acrescimo=_decimal(acrescimo, campo="acrescimo", casas="0.01"),
        observacao=(observacao or "").strip(),
    )
    item.save()

    if reservar_estoque:
        from .estoque import reservar_estoque_item

        reservar_estoque_item(
            item=item,
            usuario=usuario,
            expira_em=expira_em,
            request=request,
        )

    return item


@transaction.atomic
def alterar_item_venda(
    *,
    item,
    quantidade=None,
    preco_unitario=None,
    desconto=None,
    acrescimo=None,
    observacao=None,
    sincronizar_estoque=True,
    usuario=None,
    expira_em=None,
    request=None,
):
    item = ItemVenda.objects.select_for_update().select_related("venda", "produto").get(pk=item.pk)
    _validar_venda_editavel(item.venda)
    if item.cancelado:
        raise ValidationError({"item": "Um item cancelado nao pode ser alterado."})
    if quantidade is not None:
        item.quantidade = _decimal(quantidade, campo="quantidade", casas="0.001")
    if preco_unitario is not None:
        item.preco_unitario = _decimal(preco_unitario, campo="preco_unitario", casas="0.01")
    if desconto is not None:
        item.desconto = _decimal(desconto, campo="desconto", casas="0.01")
    if acrescimo is not None:
        item.acrescimo = _decimal(acrescimo, campo="acrescimo", casas="0.01")
    if observacao is not None:
        item.observacao = (observacao or "").strip()
    item.save()

    if sincronizar_estoque:
        from .estoque import reservar_estoque_item

        reservar_estoque_item(
            item=item,
            usuario=usuario,
            expira_em=expira_em,
            request=request,
        )

    return item


@transaction.atomic
def cancelar_item_venda(*, item, motivo, usuario=None, request=None):
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo": "Informe o motivo do cancelamento."})
    item = ItemVenda.objects.select_for_update().select_related("venda", "produto").get(pk=item.pk)
    _validar_venda_editavel(item.venda)
    if item.cancelado:
        return item
    from .estoque import liberar_reserva_item

    liberar_reserva_item(
        item=item,
        usuario=usuario,
        request=request,
    )

    item.cancelado = True
    item.motivo_cancelamento = motivo
    item.cancelado_por = usuario
    item.cancelado_em = timezone.now()
    item.save()
    return item


@transaction.atomic
def recalcular_venda(*, venda):
    venda = Venda.objects.select_for_update().get(pk=venda.pk)
    venda.recalcular_totais()
    return venda
