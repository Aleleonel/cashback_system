from decimal import Decimal

from django.db.models import F, Min, Sum
from django.utils import timezone

from vouchers.models import UsoVoucher

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
        'loja'
    ).order_by(
        'data_expiracao',
        'data_liberacao',
        'criado_em'
    )


def get_saldo_disponivel_cliente(*, matriz, cliente):
    total = get_lancamentos_disponiveis_cliente(
        matriz=matriz,
        cliente=cliente
    ).aggregate(
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
            'voucher_codigo': None,
            'voucher_nome': None,
            'desconto_voucher': None,
            'referencia': lancamento,
        })

    usos_cashback = UsoCashback.objects.filter(
        matriz=matriz,
        cliente=cliente
    ).select_related(
        'loja'
    ).order_by(
        'data_uso'
    )

    for uso in usos_cashback:
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
            'voucher_codigo': None,
            'voucher_nome': None,
            'desconto_voucher': None,
            'referencia': uso,
        })

    usos_voucher = UsoVoucher.objects.filter(
        matriz=matriz,
        cliente=cliente
    ).select_related(
        'loja',
        'voucher',
        'compra',
    ).order_by(
        'criado_em'
    )

    for uso in usos_voucher:
        compra = uso.compra

        movimentacoes.append({
            'data': uso.criado_em,
            'tipo': 'BENEFICIO',
            'titulo': 'Voucher utilizado',
            'loja': uso.loja,
            'entrada': Decimal('0.00'),
            'saida': Decimal('0.00'),
            'valor_compra': uso.valor_compra,
            'valor_base_cashback': (
                compra.valor_base_cashback
                if compra
                else None
            ),
            'percentual_cashback': (
                compra.percentual_cashback
                if compra
                else None
            ),
            'observacao': uso.observacao or '',
            'voucher_codigo': uso.voucher.codigo,
            'voucher_nome': uso.voucher.nome,
            'desconto_voucher': uso.valor_desconto,
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


def get_resumo_extrato_cliente(*, matriz, cliente):
    hoje = timezone.localdate()

    saldo_disponivel = get_saldo_disponivel_cliente(
        matriz=matriz,
        cliente=cliente,
    )

    ultima_compra = LancamentoCashback.objects.filter(
        matriz=matriz,
        cliente=cliente,
    ).order_by(
        '-data_compra',
        '-criado_em',
    ).first()

    proxima_liberacao = (
        LancamentoCashback.objects.filter(
            matriz=matriz,
            cliente=cliente,
            data_liberacao__gt=hoje,
        ).aggregate(
            data=Min('data_liberacao')
        )['data']
    )

    proxima_expiracao = (
        LancamentoCashback.objects.filter(
            matriz=matriz,
            cliente=cliente,
            data_expiracao__gte=hoje,
            valor_cashback__gt=F('valor_utilizado'),
        ).aggregate(
            data=Min('data_expiracao')
        )['data']
    )

    cashback_a_liberar = (
        LancamentoCashback.objects.filter(
            matriz=matriz,
            cliente=cliente,
            data_liberacao__gt=hoje,
        ).aggregate(
            total=Sum(F('valor_cashback') - F('valor_utilizado'))
        )['total']
        or Decimal('0.00')
    )

    total_gerado = (
        LancamentoCashback.objects.filter(
            matriz=matriz,
            cliente=cliente,
        ).aggregate(
            total=Sum('valor_cashback')
        )['total']
        or Decimal('0.00')
    )

    total_utilizado = (
        UsoCashback.objects.filter(
            matriz=matriz,
            cliente=cliente,
        ).aggregate(
            total=Sum('valor_usado')
        )['total']
        or Decimal('0.00')
    )

    return {
        'saldo_disponivel': saldo_disponivel,
        'ultima_compra': ultima_compra,
        'proxima_liberacao': proxima_liberacao,
        'proxima_expiracao': proxima_expiracao,
        'cashback_a_liberar': cashback_a_liberar,
        'total_gerado': total_gerado,
        'total_utilizado': total_utilizado,
    }