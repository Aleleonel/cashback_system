from django.core.exceptions import ValidationError
from django.db import transaction

from pdv.choices import StatusOperacaoVenda
from pdv.models import Venda

from .itens import cancelar_item_venda


@transaction.atomic
def cancelar_venda(
    *,
    venda,
    usuario=None,
    request=None,
    motivo="Venda cancelada na frente de caixa.",
):
    venda = (
        Venda.objects
        .select_for_update()
        .select_related(
            "matriz",
            "loja",
            "cliente",
            "operador",
            "vendedor",
            "sessao_caixa",
        )
        .get(pk=venda.pk)
    )

    if venda.status == StatusOperacaoVenda.FINALIZADA:
        raise ValidationError({
            "venda": "Venda finalizada nao pode ser cancelada por esta tela."
        })

    if venda.status == StatusOperacaoVenda.CANCELADA:
        return venda

    itens = (
        venda.itens
        .select_for_update()
        .filter(cancelado=False)
        .select_related("produto")
        .order_by("sequencia")
    )

    for item in itens:
        cancelar_item_venda(
            item=item,
            motivo=motivo,
            usuario=usuario,
            request=request,
        )

    venda.pagamentos.all().delete()
    venda.status = StatusOperacaoVenda.CANCELADA
    venda.recalcular_totais(salvar=False)
    venda.full_clean()
    venda.save(
        update_fields=[
            "status",
            "subtotal",
            "desconto",
            "acrescimo",
            "total",
            "quantidade_itens",
            "atualizada_em",
        ]
    )

    return venda