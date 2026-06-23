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

    cashback_base = LancamentoCashback.objects.filter(
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

    ultimos_clientes = clientes_base.filter(
        ativo=True
    ).only(
        'id',
        'nome',
        'cpf',
        'telefone',
        'criado_em',
    ).order_by(
        '-criado_em'
    )[:5]

    ultimas_compras = cashback_base.select_related(
        'cliente',
        'loja'
    ).only(
        'id',
        'cliente__nome',
        'loja__nome',
        'valor_compra',
        'valor_cashback',
        'data_compra',
        'criado_em',
    ).order_by(
        '-criado_em'
    )[:5]

    top_clientes_cashback = cashback_base.values(
        'cliente__id',
        'cliente__nome',
        'cliente__cpf',
    ).annotate(
        total_cashback=Sum('valor_cashback'),
        total_utilizado=Sum('valor_utilizado'),
        total_restante=Sum(F('valor_cashback') - F('valor_utilizado')),
        total_compras=Count('id'),
    ).order_by(
        '-total_cashback'
    )[:10]

    return {
        'total_clientes': total_clientes,
        'clientes_ativos': clientes_ativos,
        'aniversariantes_mes': aniversariantes_mes,
        'cashback_emitido': cashback_emitido,
        'cashback_utilizado': cashback_utilizado,
        'cashback_disponivel': cashback_disponivel,
        'ultimos_clientes': ultimos_clientes,
        'ultimas_compras': ultimas_compras,
        'top_clientes_cashback': top_clientes_cashback,
    }