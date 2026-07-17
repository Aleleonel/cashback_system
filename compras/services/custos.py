from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from produtos.models import Produto


CENTAVOS = Decimal('0.01')
ZERO = Decimal('0.00')


def calcular_custo_unitario_item(
    *,
    item_pedido,
    subtotal_pedido,
    quantidade_total_pedido,
    frete,
    desconto,
):
    """
    Calcula o custo unitario efetivo do item.

    Regra principal:
    - frete e desconto sao rateados pelo valor do item;
    - quando todos os itens possuem valor zero, o rateio usa quantidade;
    - o resultado final e arredondado para centavos.
    """
    valor_unitario = Decimal(item_pedido.valor_unitario)
    quantidade_item = Decimal(item_pedido.quantidade)
    subtotal_item = Decimal(item_pedido.subtotal)
    ajuste_total = Decimal(frete) - Decimal(desconto)

    if quantidade_item <= Decimal('0.000'):
        raise ValidationError({
            'quantidade': 'A quantidade do item deve ser positiva.'
        })

    if subtotal_pedido > ZERO:
        proporcao = subtotal_item / subtotal_pedido
    elif quantidade_total_pedido > Decimal('0.000'):
        proporcao = quantidade_item / quantidade_total_pedido
    else:
        raise ValidationError({
            'itens': 'Nao foi possivel ratear os custos do pedido.'
        })

    ajuste_item = ajuste_total * proporcao
    custo_total_item = subtotal_item + ajuste_item

    custo_unitario = (
        custo_total_item / quantidade_item
    ).quantize(
        CENTAVOS,
        rounding=ROUND_HALF_UP,
    )

    return max(custo_unitario, ZERO)


@transaction.atomic
def atualizar_custos_produtos_recebimento(
    *,
    pedido,
    itens_recebidos,
    usuario,
    loja,
    request=None,
):
    """
    Atualiza Produto.custo_base para os produtos recebidos.

    O custo e baseado no pedido completo. Portanto, recebimentos
    parciais do mesmo pedido produzem o mesmo custo unitario.
    """
    itens_pedido = list(
        pedido.itens
        .select_related('produto')
        .order_by('pk')
    )

    subtotal_pedido = sum(
        (
            Decimal(item.subtotal)
            for item in itens_pedido
        ),
        ZERO,
    )

    quantidade_total_pedido = sum(
        (
            Decimal(item.quantidade)
            for item in itens_pedido
        ),
        Decimal('0.000'),
    )

    ids_recebidos = {
        int(item['item_pedido_id'])
        for item in itens_recebidos
    }

    custos_atualizados = []

    for item in itens_pedido:
        if item.pk not in ids_recebidos:
            continue

        custo_anterior = Decimal(item.produto.custo_base)
        custo_novo = calcular_custo_unitario_item(
            item_pedido=item,
            subtotal_pedido=subtotal_pedido,
            quantidade_total_pedido=quantidade_total_pedido,
            frete=pedido.frete,
            desconto=pedido.desconto,
        )

        produto = (
            Produto.objects
            .select_for_update()
            .get(
                pk=item.produto_id,
                matriz=pedido.matriz,
            )
        )

        produto.custo_base = custo_novo
        produto.save(
            update_fields=[
                'custo_base',
                'atualizado_em',
            ]
        )

        registrar_auditoria(
            usuario=usuario,
            matriz=pedido.matriz,
            loja=loja,
            acao=RegistroAuditoria.ACAO_EDITAR,
            recurso='produtos.produto',
            recurso_id=produto.uuid,
            descricao=(
                f'Custo atualizado por recebimento de compra; '
                f'pedido=PC-{pedido.numero:06d}; '
                f'produto={produto}; '
                f'custo_anterior={custo_anterior}; '
                f'custo_novo={custo_novo}.'
            ),
            request=request,
        )

        custos_atualizados.append({
            'produto_id': produto.pk,
            'custo_anterior': custo_anterior,
            'custo_novo': custo_novo,
        })

    return custos_atualizados