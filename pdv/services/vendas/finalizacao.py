from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from estoque.services import confirmar_reserva_estoque
from pdv.choices import StatusOperacaoVenda
from pdv.models import Venda
from pdv.services.cliente_consumidor import obter_ou_criar_cliente_consumidor

from .auditoria import registrar_auditoria_finalizacao_venda
from .caixa import registrar_movimentacao_caixa_venda
from .estoque import obter_reserva_ativa_item
from .validacoes import validar_venda_para_finalizacao


def _associar_cliente_consumidor(*, venda):
    if venda.cliente_id:
        return venda

    venda.cliente = obter_ou_criar_cliente_consumidor(
        matriz=venda.matriz,
        loja=venda.loja,
    )
    venda.save(update_fields=["cliente", "atualizada_em"])
    return venda


def _confirmar_reservas(*, venda, usuario=None, request=None):
    resultados = []

    itens = (
        venda.itens
        .filter(cancelado=False)
        .select_related("produto")
        .order_by("sequencia")
    )

    for item in itens:
        if not item.produto.controla_estoque:
            continue

        reserva = obter_reserva_ativa_item(item=item)
        if reserva is None:
            raise ValidationError({
                "estoque": (
                    f"O item {item.sequencia} nao possui uma reserva "
                    "de estoque ativa."
                )
            })

        resultado = confirmar_reserva_estoque(
            reserva=reserva,
            usuario=usuario,
            request=request,
        )
        resultados.append(resultado)

    return resultados


def _finalizar_modelo(*, venda):
    venda.status = StatusOperacaoVenda.FINALIZADA
    venda.finalizada_em = timezone.now()
    venda.full_clean()
    venda.save(
        update_fields=[
            "cliente",
            "status",
            "finalizada_em",
            "subtotal",
            "desconto",
            "acrescimo",
            "total",
            "quantidade_itens",
            "atualizada_em",
        ]
    )
    return venda


@transaction.atomic
def finalizar_venda(*, venda, usuario=None, request=None):
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
            "sessao_caixa__caixa",
        )
        .get(pk=venda.pk)
    )

    if venda.status == StatusOperacaoVenda.FINALIZADA:
        return venda

    _associar_cliente_consumidor(venda=venda)
    validar_venda_para_finalizacao(venda=venda)

    _confirmar_reservas(
        venda=venda,
        usuario=usuario,
        request=request,
    )

    movimentacao_caixa = registrar_movimentacao_caixa_venda(
        venda=venda,
        operador=venda.operador,
    )

    _finalizar_modelo(venda=venda)

    registrar_auditoria_finalizacao_venda(
        venda=venda,
        usuario=usuario or venda.operador,
        movimentacao_caixa=movimentacao_caixa,
        request=request,
    )

    return venda
