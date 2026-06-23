from decimal import Decimal

from django.db.models import Sum, F
from django.utils import timezone

from .models import LancamentoCashback


def get_lancamentos_disponiveis_cliente(*, matriz, cliente):
    hoje = timezone.localdate()

    return LancamentoCashback.objects.filter(
        matriz=matriz,
        cliente=cliente,
        data_liberacao__lte=hoje,
        data_expiracao__gte=hoje,
        valor_cashback__gt=F('valor_utilizado'),
    ).select_related(
        'matriz',
        'loja',
        'cliente'
    ).order_by(
        'data_expiracao',
        'data_liberacao',
        'criado_em'
    )


def get_saldo_disponivel_cliente(*, matriz, cliente):
    lancamentos = get_lancamentos_disponiveis_cliente(
        matriz=matriz,
        cliente=cliente
    )

    total = lancamentos.aggregate(
        total=Sum(F('valor_cashback') - F('valor_utilizado'))
    )['total']

    return total or Decimal('0.00')


def get_extrato_cliente(*, matriz, cliente):
    return LancamentoCashback.objects.filter(
        matriz=matriz,
        cliente=cliente
    ).select_related(
        'loja'
    ).only(
        'id',
        'loja__nome',
        'valor_compra',
        'percentual_cashback',
        'valor_cashback',
        'valor_utilizado',
        'data_compra',
        'data_liberacao',
        'data_expiracao',
        'criado_em',
    ).order_by(
        '-data_compra',
        '-criado_em'
    )