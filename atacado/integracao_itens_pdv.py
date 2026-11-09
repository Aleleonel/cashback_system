"""F32P3G: prepara itens do pedido para venda PDV sem efeitos colaterais."""
from decimal import Decimal
from django.core.exceptions import ValidationError
from .integracao_totais import dinheiro, conciliar_total_pedido


def preparar_itens_pdv(*, pedido):
    """Retorna (itens, ajustes). Nao cria vendas, reservas ou pagamentos."""
    itens_origem = list(pedido.itens.all().order_by("pk"))
    if not itens_origem:
        raise ValidationError({"itens": "Pedido sem itens."})
    itens = []
    subtotal = Decimal("0.00")
    for seq, item in enumerate(itens_origem, 1):
        quantidade = Decimal(str(item.quantidade))
        if not quantidade.is_finite() or quantidade <= 0 or quantidade.as_tuple().exponent < -3:
            raise ValidationError({"quantidade": "Quantidade invalida para o PDV."})
        preco = dinheiro(item.preco_unitario_final, "preco_unitario_final")
        if preco < 0:
            raise ValidationError({"preco_unitario_final": "Preco negativo."})
        valor = (quantidade * preco).quantize(Decimal("0.01"))
        subtotal += valor
        itens.append({"produto_id": item.produto_id, "sequencia": seq,
                      "quantidade": quantidade, "preco_unitario": preco,
                      "subtotal": valor, "desconto": Decimal("0.00"),
                      "acrescimo": Decimal("0.00"), "total": valor})
    total = dinheiro(pedido.total, "total")
    if total < 0:
        raise ValidationError({"total": "Total negativo."})
    # A diferenca e explicita: inclui frete, descontos e ajustes ja negociados.
    diferenca = total - subtotal
    desconto = max(-diferenca, Decimal("0.00"))
    acrescimo = max(diferenca, Decimal("0.00"))
    conciliar_total_pedido(subtotal_itens=subtotal, desconto=desconto,
                           acrescimo=acrescimo, total_pedido=total)
    return itens, {"subtotal": subtotal, "desconto_geral": desconto,
                   "acrescimo_geral": acrescimo, "total": total}
