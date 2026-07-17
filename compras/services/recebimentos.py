from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models, transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from estoque.choices import (
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.services import registrar_entrada_estoque

from compras.choices import StatusPedidoCompra
from compras.models import (
    ItemPedidoCompra,
    ItemRecebimentoCompra,
    PedidoCompra,
    RecebimentoCompra,
)


@transaction.atomic
def receber_pedido_compra(
    *,
    pedido,
    loja,
    itens,
    chave_idempotencia,
    usuario,
    documento_referencia='',
    observacoes='',
    request=None,
):
    chave_idempotencia = (chave_idempotencia or '').strip()

    if not chave_idempotencia:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotencia e obrigatoria.'
            )
        })

    pedido = (
        PedidoCompra.objects
        .select_for_update()
        .select_related('matriz', 'fornecedor')
        .get(pk=pedido.pk)
    )

    if loja.matriz_id != pedido.matriz_id:
        raise ValidationError({
            'loja': 'A loja nao pertence a matriz do pedido.'
        })

    if pedido.status not in {
        StatusPedidoCompra.ENVIADO,
        StatusPedidoCompra.PARCIAL,
    }:
        raise ValidationError(
            'Somente pedidos enviados ou parcialmente '
            'recebidos podem ser recebidos.'
        )

    existente = (
        RecebimentoCompra.objects
        .filter(
            matriz=pedido.matriz,
            chave_idempotencia=chave_idempotencia,
        )
        .first()
    )

    if existente is not None:
        return existente

    itens = _normalizar_itens(itens)

    if not itens:
        raise ValidationError({
            'itens': 'Informe ao menos um item.'
        })

    recebimento = RecebimentoCompra.objects.create(
        matriz=pedido.matriz,
        loja=loja,
        pedido=pedido,
        chave_idempotencia=chave_idempotencia,
        documento_referencia=(
            documento_referencia or ''
        ).strip(),
        observacoes=(observacoes or '').strip(),
        recebido_por=usuario,
    )

    for posicao, dados in enumerate(itens, start=1):
        item = (
            ItemPedidoCompra.objects
            .select_for_update()
            .select_related('produto')
            .get(
                pk=dados['item_pedido_id'],
                pedido=pedido,
            )
        )

        quantidade = dados['quantidade']
        pendente = (
            item.quantidade
            - item.quantidade_recebida
        )

        if quantidade > pendente:
            raise ValidationError({
                'quantidade': (
                    f'{item.produto}: quantidade superior '
                    f'ao pendente de {pendente}.'
                )
            })

        resultado = registrar_entrada_estoque(
            matriz=pedido.matriz,
            loja=loja,
            produto=item.produto,
            tipo=TipoMovimentacao.COMPRA,
            origem=OrigemMovimentacao.COMPRA,
            quantidade=quantidade,
            chave_idempotencia=(
                f'compra:{recebimento.uuid}:{posicao}'
            ),
            usuario=usuario,
            observacao=(
                f'Recebimento PC-{pedido.numero:06d}.'
            ),
            documento_referencia=(
                recebimento.documento_referencia
            ),
            origem_id=str(recebimento.uuid),
            request=request,
        )

        ItemRecebimentoCompra.objects.create(
            recebimento=recebimento,
            item_pedido=item,
            quantidade=quantidade,
            movimentacao_estoque=resultado.movimentacao,
        )

        item.quantidade_recebida += quantidade
        item.save(
            update_fields=[
                'quantidade_recebida',
                'atualizado_em',
            ]
        )

    possui_pendente = (
        ItemPedidoCompra.objects
        .filter(
            pedido=pedido,
            quantidade_recebida__lt=models.F(
                'quantidade'
            ),
        )
        .exists()
    )

    pedido.status = (
        StatusPedidoCompra.PARCIAL
        if possui_pendente
        else StatusPedidoCompra.RECEBIDO
    )
    pedido.save(
        update_fields=['status', 'atualizado_em']
    )

    registrar_auditoria(
        usuario=usuario,
        matriz=pedido.matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='compras.recebimento_compra',
        recurso_id=recebimento.uuid,
        descricao=(
            f'Recebimento do pedido '
            f'PC-{pedido.numero:06d}; '
            f'status={pedido.status}.'
        ),
        request=request,
    )

    return recebimento


def _normalizar_itens(itens):
    resultado = []

    for item in itens or []:
        try:
            quantidade = Decimal(
                str(item.get('quantidade') or 0)
            ).quantize(Decimal('0.001'))

            if not quantidade.is_finite():
                raise InvalidOperation
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as erro:
            raise ValidationError({
                'quantidade': (
                    'Informe uma quantidade valida.'
                )
            }) from erro

        if quantidade < Decimal('0.000'):
            raise ValidationError({
                'quantidade': (
                    'A quantidade nao pode ser negativa.'
                )
            })

        if quantidade == Decimal('0.000'):
            continue

        resultado.append({
            'item_pedido_id': int(
                item['item_pedido_id']
            ),
            'quantidade': quantidade,
        })

    return resultado
