from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from estoque.choices import StatusReservaEstoque
from estoque.models import ReservaEstoque, SaldoEstoque


ZERO_ESTOQUE = Decimal('0.000')


def get_quantidade_reservada(
    *,
    matriz,
    loja,
    produto,
):
    return (
        ReservaEstoque.objects
        .filter(
            matriz=matriz,
            loja=loja,
            produto=produto,
            status=StatusReservaEstoque.ATIVA,
        )
        .aggregate(
            total=Coalesce(
                Sum('quantidade'),
                Value(
                    ZERO_ESTOQUE,
                    output_field=DecimalField(
                        max_digits=15,
                        decimal_places=3,
                    ),
                ),
            )
        )['total']
    )


def get_saldo_disponivel(
    *,
    matriz,
    loja,
    produto,
):
    saldo_fisico = (
        SaldoEstoque.objects
        .filter(
            matriz=matriz,
            loja=loja,
            produto=produto,
        )
        .values_list(
            'quantidade_atual',
            flat=True,
        )
        .first()
    )

    if saldo_fisico is None:
        saldo_fisico = ZERO_ESTOQUE

    quantidade_reservada = get_quantidade_reservada(
        matriz=matriz,
        loja=loja,
        produto=produto,
    )

    return saldo_fisico - quantidade_reservada
