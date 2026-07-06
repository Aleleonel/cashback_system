from decimal import Decimal

from django.db.models import Sum, F
from django.utils import timezone

from .models import (
    LancamentoCashback,
    UsoCashback,
)


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
        'valor_base_cashback',
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


def get_movimentacoes_cliente(*, matriz, cliente):
    movimentacoes = []

    lancamentos = LancamentoCashback.objects.filter(
        matriz=matriz,
        cliente=cliente
    ).select_related(
        'loja'
    ).order_by(
        'criado_em'
    )

    for lancamento in lancamentos:
        movimentacoes.append({
            'data': lancamento.criado_em,
            'tipo': 'ENTRADA',
            'titulo': 'Cashback gerado',
            'loja': lancamento.loja,
            'entrada': lancamento.valor_cashback,
            'saida': Decimal('0.00'),
            'valor_compra': lancamento.valor_compra,
            'valor_base_cashback': lancamento.valor_base_cashback,
            'percentual_cashback': lancamento.percentual_cashback,
            'observacao': lancamento.observacao or '',
            'referencia': lancamento,
        })

    usos = UsoCashback.objects.filter(
        matriz=matriz,
        cliente=cliente
    ).select_related(
        'loja'
    ).order_by(
        'data_uso'
    )

    for uso in usos:
        movimentacoes.append({
            'data': uso.data_uso,
            'tipo': 'SAIDA',
            'titulo': 'Cashback utilizado',
            'loja': uso.loja,
            'entrada': Decimal('0.00'),
            'saida': uso.valor_usado,
            'valor_compra': None,
            'valor_base_cashback': None,
            'percentual_cashback': None,
            'observacao': uso.observacao or '',
            'referencia': uso,
        })

    movimentacoes = sorted(
        movimentacoes,
        key=lambda item: item['data']
    )

    saldo = Decimal('0.00')

    for item in movimentacoes:
        saldo += item['entrada']
        saldo -= item['saida']
        item['saldo'] = saldo

    return list(reversed(movimentacoes))