"""Consultas para o dashboard de estoque."""

from django.db.models import Sum
from django.db.models.functions import Coalesce

from estoque.models import SaldoEstoque
from produtos.models import Produto

from decimal import Decimal
from django.db.models import DecimalField


def get_indicadores_dashboard_estoque(*, matriz):
    """
    Retorna indicadores consolidados da matriz.

    Um produto é considerado com estoque quando a soma dos saldos de todas
    as lojas da matriz é maior que zero. Produtos controlados sem saldo ou
    com saldo consolidado igual a zero são considerados sem estoque.
    """
    produtos_controlados = Produto.objects.filter(
        matriz=matriz,
        controla_estoque=True,
    )

    total_produtos_controlados = produtos_controlados.count()

    saldos_por_produto = (
        SaldoEstoque.objects
        .filter(
            matriz=matriz,
            produto__controla_estoque=True,
        )
        .values('produto_id')
        .annotate(
            quantidade_consolidada=Coalesce(
                Sum("quantidade_atual"),
                Decimal("0.000"),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=3,
                ),
            )
        )
    )

    produtos_com_estoque = saldos_por_produto.filter(
        quantidade_consolidada__gt=0
    ).count()

    saldo_consolidado = (
        SaldoEstoque.objects
        .filter(
            matriz=matriz,
            produto__controla_estoque=True,
        )
        .aggregate(
            total=Coalesce(
                Sum("quantidade_atual"),
                Decimal("0.000"),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=3,
                ),
            )
        )['total']
    )

    return {
        'saldo_consolidado': saldo_consolidado,
        'produtos_controlados': total_produtos_controlados,
        'produtos_com_estoque': produtos_com_estoque,
        'produtos_sem_estoque': (
            total_produtos_controlados - produtos_com_estoque
        ),
    }