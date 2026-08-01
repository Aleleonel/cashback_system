"""Consultas para o dashboard de estoque."""

from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce

from estoque.models import SaldoEstoque
from produtos.models import Produto


QUANTIDADE_OUTPUT_FIELD = DecimalField(
    max_digits=15,
    decimal_places=3,
)

VALOR_OUTPUT_FIELD = DecimalField(
    max_digits=27,
    decimal_places=5,
)


def get_indicadores_dashboard_estoque(*, matriz):
    """
    Retorna indicadores consolidados da matriz.

    A quantidade total corresponde à soma dos saldos atuais de todas as
    lojas. Os valores financeiros são estimativas calculadas com o custo
    base e o preço de venda atuais do cadastro de cada produto.
    """
    produtos_controlados = Produto.objects.filter(
        matriz=matriz,
        controla_estoque=True,
    )

    total_produtos_controlados = produtos_controlados.count()

    saldos = SaldoEstoque.objects.filter(
        matriz=matriz,
        produto__controla_estoque=True,
    )

    saldos_por_produto = (
        saldos
        .values('produto_id')
        .annotate(
            quantidade_consolidada=Coalesce(
                Sum('quantidade_atual'),
                Decimal('0.000'),
                output_field=QUANTIDADE_OUTPUT_FIELD,
            )
        )
    )

    produtos_com_estoque = saldos_por_produto.filter(
        quantidade_consolidada__gt=0
    ).count()

    valor_custo_item = ExpressionWrapper(
        F('quantidade_atual') * F('produto__custo_base'),
        output_field=VALOR_OUTPUT_FIELD,
    )
    valor_venda_item = ExpressionWrapper(
        F('quantidade_atual') * F('produto__preco_venda'),
        output_field=VALOR_OUTPUT_FIELD,
    )

    totais = saldos.aggregate(
        quantidade_total=Coalesce(
            Sum('quantidade_atual'),
            Decimal('0.000'),
            output_field=QUANTIDADE_OUTPUT_FIELD,
        ),
        valor_estoque_custo=Coalesce(
            Sum(valor_custo_item),
            Decimal('0.00'),
            output_field=VALOR_OUTPUT_FIELD,
        ),
        valor_potencial_venda=Coalesce(
            Sum(valor_venda_item),
            Decimal('0.00'),
            output_field=VALOR_OUTPUT_FIELD,
        ),
    )

    return {
        'quantidade_total': totais['quantidade_total'],
        # Compatibilidade temporária com referências anteriores.
        'saldo_consolidado': totais['quantidade_total'],
        'valor_estoque_custo': totais['valor_estoque_custo'],
        'valor_potencial_venda': totais['valor_potencial_venda'],
        'produtos_controlados': total_produtos_controlados,
        'produtos_com_estoque': produtos_com_estoque,
        'produtos_sem_estoque': (
            total_produtos_controlados - produtos_com_estoque
        ),
    }