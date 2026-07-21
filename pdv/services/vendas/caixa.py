from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from pdv.choices import StatusSessaoCaixa, TipoMovimentacaoCaixa
from pdv.models import MovimentacaoCaixa, Venda


def calcular_valor_movimenta_caixa(*, venda):
    total = Decimal("0.00")

    pagamentos = (
        venda.pagamentos
        .select_related("forma_pagamento")
        .filter(forma_pagamento__movimenta_caixa=True)
        .order_by("criado_em")
    )

    for pagamento in pagamentos:
        total += pagamento.valor

    return total.quantize(Decimal("0.01"))


@transaction.atomic
def registrar_movimentacao_caixa_venda(*, venda, operador):
    venda = (
        Venda.objects
        .select_for_update()
        .select_related("sessao_caixa")
        .get(pk=venda.pk)
    )

    sessao = venda.sessao_caixa
    if sessao is None:
        raise ValidationError({
            "sessao_caixa": "A venda deve possuir uma sessao de caixa."
        })

    if sessao.status != StatusSessaoCaixa.ABERTA:
        raise ValidationError({
            "sessao_caixa": "A sessao de caixa deve estar aberta."
        })

    valor = calcular_valor_movimenta_caixa(venda=venda)

    existente = (
        MovimentacaoCaixa.objects
        .select_for_update()
        .filter(
            venda=venda,
            tipo=TipoMovimentacaoCaixa.VENDA,
        )
        .first()
    )

    if existente is not None:
        if (
            existente.sessao_caixa_id != sessao.pk
            or existente.valor != valor
        ):
            raise ValidationError({
                "movimentacao_caixa": (
                    "Ja existe uma movimentacao de caixa incompatível "
                    "para esta venda."
                )
            })
        return existente

    if valor <= Decimal("0.00"):
        return None

    movimentacao = MovimentacaoCaixa(
        sessao_caixa=sessao,
        tipo=TipoMovimentacaoCaixa.VENDA,
        valor=valor,
        operador=operador,
        venda=venda,
        descricao=f"Recebimento da venda {venda.uuid}.",
    )
    movimentacao.full_clean()
    movimentacao.save()

    return movimentacao
