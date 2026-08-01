
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from estoque.choices import (
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.services import registrar_saida_estoque

from compras.models import (
    DevolucaoCompra,
    ItemDevolucaoCompra,
    ItemRecebimentoCompra,
    RecebimentoCompra,
)


@transaction.atomic
def devolver_recebimento_compra(
    *,
    recebimento,
    itens,
    chave_idempotencia,
    usuario,
    documento_referencia='',
    motivo='',
    request=None,
):
    chave_idempotencia = (chave_idempotencia or '').strip()
    motivo = (motivo or '').strip()

    if not chave_idempotencia:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotencia e obrigatoria.'
            )
        })

    if not motivo:
        raise ValidationError({
            'motivo': 'Informe o motivo da devolucao.'
        })

    recebimento = (
        RecebimentoCompra.objects
        .select_for_update()
        .select_related(
            'matriz',
            'loja',
            'pedido',
            'pedido__fornecedor',
        )
        .get(pk=recebimento.pk)
    )

    existente = (
        DevolucaoCompra.objects
        .filter(
            matriz=recebimento.matriz,
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

    ids = [
        item['item_recebimento_id']
        for item in itens
    ]

    if len(ids) != len(set(ids)):
        raise ValidationError({
            'itens': 'Item informado mais de uma vez.'
        })

    devolucao = DevolucaoCompra.objects.create(
        matriz=recebimento.matriz,
        loja=recebimento.loja,
        recebimento=recebimento,
        chave_idempotencia=chave_idempotencia,
        documento_referencia=(
            documento_referencia or ''
        ).strip(),
        motivo=motivo,
        devolvido_por=usuario,
    )

    for posicao, dados in enumerate(itens, start=1):
        item = (
            ItemRecebimentoCompra.objects
            .select_for_update()
            .select_related(
                'item_pedido__produto',
                'movimentacao_estoque',
            )
            .get(
                pk=dados['item_recebimento_id'],
                recebimento=recebimento,
            )
        )

        quantidade = dados['quantidade']
        disponivel = (
            item.quantidade
            - item.quantidade_devolvida
        )

        if quantidade > disponivel:
            raise ValidationError({
                'quantidade': (
                    f'{item.item_pedido.produto}: quantidade '
                    f'superior ao disponivel de {disponivel}.'
                )
            })

        resultado = registrar_saida_estoque(
            matriz=recebimento.matriz,
            loja=recebimento.loja,
            produto=item.item_pedido.produto,
            tipo=TipoMovimentacao.DEVOLUCAO_COMPRA,
            origem=OrigemMovimentacao.COMPRA,
            quantidade=quantidade,
            chave_idempotencia=(
                f'devolucao-compra:{devolucao.uuid}:{posicao}'
            ),
            usuario=usuario,
            observacao=(
                f'Devolucao do recebimento {recebimento.id}; '
                f'pedido PC-{recebimento.pedido.numero:06d}; '
                f'motivo: {motivo}'
            ),
            documento_referencia=(
                devolucao.documento_referencia
            ),
            origem_id=str(devolucao.uuid),
            request=request,
        )

        ItemDevolucaoCompra.objects.create(
            devolucao=devolucao,
            item_recebimento=item,
            quantidade=quantidade,
            movimentacao_estoque=resultado.movimentacao,
        )

        item.quantidade_devolvida += quantidade
        item.save(update_fields=['quantidade_devolvida'])

    registrar_auditoria(
        usuario=usuario,
        matriz=recebimento.matriz,
        loja=recebimento.loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='compras.devolucao_compra',
        recurso_id=devolucao.uuid,
        descricao=(
            f'Devolucao ao fornecedor; '
            f'pedido=PC-{recebimento.pedido.numero:06d}; '
            f'recebimento={recebimento.id}.'
        ),
        request=request,
    )

    return devolucao


def _normalizar_itens(itens):
    resultado = []

    for item in itens or []:
        try:
            quantidade = Decimal(
                str(item.get('quantidade') or 0)
            ).quantize(Decimal('0.001'))

            if not quantidade.is_finite():
                raise InvalidOperation

            item_id = int(item['item_recebimento_id'])
        except (
            InvalidOperation,
            KeyError,
            TypeError,
            ValueError,
        ) as erro:
            raise ValidationError({
                'itens': 'Item ou quantidade invalida.'
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
            'item_recebimento_id': item_id,
            'quantidade': quantidade,
        })

    return resultado
