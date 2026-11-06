from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from configuracoes.models import ConfiguracaoComercial
from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from estoque.models import ReservaEstoque
from estoque.services import registrar_reserva_estoque, confirmar_reserva_estoque, liberar_reserva_estoque
from .models import ItemPedidoAtacado, PedidoAtacado, StatusOrcamentoAtacado, StatusPedidoAtacado
from .services import transicionar_orcamento

@transaction.atomic
def gerar_pedido_de_orcamento_aprovado(orcamento, usuario=None):
    orcamento.refresh_from_db()
    if orcamento.status != StatusOrcamentoAtacado.APROVADO:
        raise ValidationError("Somente orçamento aprovado pode gerar pedido.")
    if PedidoAtacado.objects.filter(orcamento_origem=orcamento).exists():
        raise ValidationError("Orçamento já possui pedido.")
    itens = list(orcamento.itens.all())
    if not itens:
        raise ValidationError("Orçamento sem itens não pode gerar pedido.")
    config = ConfiguracaoComercial.objects.get(matriz=orcamento.matriz)
    percentual = max([Decimal(str(i.percentual_desconto_atacado or 0)) for i in itens] or [Decimal("0")])
    pedido = PedidoAtacado.objects.create(
        orcamento_origem=orcamento, matriz=orcamento.matriz, loja=orcamento.loja,
        cliente=orcamento.cliente, vendedor=orcamento.vendedor,
        subtotal_produtos=orcamento.subtotal_produtos, desconto_atacado=orcamento.desconto_atacado,
        ajustes_negociados=orcamento.ajustes_negociados, frete=orcamento.frete, total=orcamento.total,
        percentual_desconto_snapshot=percentual,
        produto_promocional_conta_para_faixa_snapshot=config.produto_promocional_conta_para_faixa_atacado,
        observacoes_snapshot=orcamento.observacoes or "",
    )
    for i in itens:
        ItemPedidoAtacado.objects.create(
            pedido=pedido, produto=i.produto, quantidade=i.quantidade,
            preco_unitario_original=i.preco_unitario_original, preco_unitario_base=i.preco_unitario_base,
            preco_unitario_final=i.preco_unitario_final, percentual_desconto=i.percentual_desconto_atacado,
            desconto_atacado=i.desconto_atacado, ajuste_negociado=i.ajuste_negociado,
            produto_promocional_snapshot=i.produto_promocional,
            atacado_elegivel_snapshot=i.atacado_elegivel,
            conta_para_enquadramento_snapshot=i.conta_para_enquadramento,
            justificativa_negociacao_snapshot=i.justificativa_negociacao or "",
        )
    # F32J2B: pedido gerado compromete saldo disponivel sem baixar saldo fisico.
    for item_pedido in pedido.itens.select_related("produto").all():
        if not item_pedido.produto.controla_estoque:
            continue
        registrar_reserva_estoque(
            matriz=pedido.matriz,
            loja=pedido.loja,
            produto=item_pedido.produto,
            origem=OrigemMovimentacao.VENDA,
            quantidade=item_pedido.quantidade,
            chave_idempotencia=f"atacado:pedido:{pedido.pk}:item:{item_pedido.pk}",
            usuario=usuario,
            documento_referencia=f"PEDIDO-ATACADO-{pedido.pk}",
            origem_id=str(item_pedido.pk),
        )

    transicionar_orcamento(orcamento, StatusOrcamentoAtacado.PEDIDO_GERADO, usuario=usuario, observacao="Pedido de atacado gerado.")
    return pedido


def _reservas_ativas_pedido(pedido):
    return ReservaEstoque.objects.select_for_update().filter(
        matriz=pedido.matriz,
        origem=OrigemMovimentacao.VENDA,
        documento_referencia=f"PEDIDO-ATACADO-{pedido.pk}",
        status=StatusReservaEstoque.ATIVA,
    )


@transaction.atomic
def finalizar_pedido_atacado(*, pedido, usuario=None, request=None):
    pedido = PedidoAtacado.objects.select_for_update().get(pk=pedido.pk)
    if pedido.status == StatusPedidoAtacado.FINALIZADO:
        return pedido
    if pedido.status != StatusPedidoAtacado.GERADO:
        raise ValidationError({"status": "Somente pedido gerado pode ser finalizado."})
    for reserva in _reservas_ativas_pedido(pedido):
        confirmar_reserva_estoque(reserva=reserva, usuario=usuario, request=request)
    pedido.status = StatusPedidoAtacado.FINALIZADO
    pedido.finalizado_em = timezone.now()
    pedido.save(update_fields=["status", "finalizado_em"])
    return pedido


@transaction.atomic
def cancelar_pedido_atacado(*, pedido, usuario=None, request=None):
    pedido = PedidoAtacado.objects.select_for_update().get(pk=pedido.pk)
    if pedido.status == StatusPedidoAtacado.CANCELADO:
        return pedido
    if pedido.status != StatusPedidoAtacado.GERADO:
        raise ValidationError({"status": "Somente pedido gerado pode ser cancelado."})
    for reserva in _reservas_ativas_pedido(pedido):
        liberar_reserva_estoque(reserva=reserva, usuario=usuario, request=request)
    pedido.status = StatusPedidoAtacado.CANCELADO
    pedido.cancelado_em = timezone.now()
    pedido.save(update_fields=["status", "cancelado_em"])
    return pedido
