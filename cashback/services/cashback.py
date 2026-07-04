from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from cashback.models import LancamentoCashback, UsoCashback, UsoLancamentoCashback
from cashback.selectors import get_lancamentos_disponiveis_cliente


@transaction.atomic
def usar_cashback(*, matriz, loja, cliente, valor_usado, observacao=''):
    valor_restante_para_usar = Decimal(valor_usado)

    if valor_restante_para_usar <= 0:
        raise ValidationError('O valor utilizado precisa ser maior que zero.')

    lancamentos = get_lancamentos_disponiveis_cliente(
        matriz=matriz,
        cliente=cliente
    ).select_for_update()

    saldo_total = sum(l.valor_restante for l in lancamentos)

    if saldo_total < valor_restante_para_usar:
        raise ValidationError('Saldo de cashback insuficiente.')

    uso = UsoCashback.objects.create(
        matriz=matriz,
        loja=loja,
        cliente=cliente,
        valor_usado=valor_usado,
        observacao=observacao
    )

    for lancamento in lancamentos:
        if valor_restante_para_usar <= 0:
            break

        valor_disponivel = lancamento.valor_restante
        valor_a_usar = min(valor_disponivel, valor_restante_para_usar)

        UsoLancamentoCashback.objects.create(
            uso_cashback=uso,
            lancamento=lancamento,
            valor_utilizado=valor_a_usar
        )

        LancamentoCashback.objects.filter(
            id=lancamento.id
        ).update(
            valor_utilizado=F('valor_utilizado') + valor_a_usar
        )

        valor_restante_para_usar -= valor_a_usar

    return uso