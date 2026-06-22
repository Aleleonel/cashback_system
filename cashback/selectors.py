from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import LancamentoCashback


def get_saldo_disponivel_cliente(cliente):
    hoje = timezone.localdate()

    total = LancamentoCashback.objects.filter(
        cliente=cliente,
        status=LancamentoCashback.STATUS_DISPONIVEL,
        data_liberacao__lte=hoje,
        data_expiracao__gte=hoje,
    ).aggregate(
        total=Sum('valor_cashback')
    )['total']

    return total or Decimal('0.00')


def get_extrato_cliente(cliente):
    return LancamentoCashback.objects.filter(
        cliente=cliente
    ).select_related(
        'matriz',
        'loja',
        'cliente'
    ).order_by('-data_compra', '-criado_em')