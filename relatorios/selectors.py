from decimal import Decimal

from django.db.models import Count, F, Sum
from django.utils import timezone

from cashback.models import LancamentoCashback
from clientes.models import Cliente


def get_dashboard_resumo(*, matriz):

    hoje = timezone.localdate()
    mes_atual = hoje.month

    clientes_base = Cliente.objects.filter(
        matriz=matriz
    )

    total_clientes = clientes_base.count()

    clientes_ativos = clientes_base.filter(
        ativo=True
    ).count()

    aniversariantes_mes = clientes_base.filter(
        ativo=True,
        data_nascimento__month=mes_atual
    ).count()

    cashback_base = LancamentoCashback.objects.filter(
        matriz=matriz
    )

    cashback_emitido = cashback_base.aggregate(
        total=Sum('valor_cashback')
    )['total'] or Decimal('0.00')

    cashback_utilizado = cashback_base.aggregate(
        total=Sum('valor_utilizado')
    )['total'] or Decimal('0.00')

    cashback_disponivel = cashback_base.filter(
        data_liberacao__lte=hoje,
        data_expiracao__gte=hoje,
        valor_cashback__gt=F('valor_utilizado')
    ).aggregate(
        total=Sum(F('valor_cashback') - F('valor_utilizado'))
    )['total'] or Decimal('0.00')

    return {
        'total_clientes': total_clientes,
        'clientes_ativos': clientes_ativos,
        'aniversariantes_mes': aniversariantes_mes,
        'cashback_emitido': cashback_emitido,
        'cashback_utilizado': cashback_utilizado,
        'cashback_disponivel': cashback_disponivel,
    }