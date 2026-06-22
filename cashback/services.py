from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.models import ConfiguracaoSistema
from .models import LancamentoCashback


def calcular_cashback(valor_compra, percentual):
    valor = Decimal(valor_compra)
    percentual = Decimal(percentual)

    return (valor * percentual / Decimal('100')).quantize(Decimal('0.01'))


@transaction.atomic
def criar_lancamento_cashback(*, matriz, loja, cliente, valor_compra, observacao=''):
    configuracao = ConfiguracaoSistema.objects.get(matriz=matriz)

    hoje = timezone.localdate()

    valor_cashback = calcular_cashback(
        valor_compra=valor_compra,
        percentual=configuracao.percentual_cashback
    )

    lancamento = LancamentoCashback.objects.create(
        matriz=matriz,
        loja=loja,
        cliente=cliente,
        valor_compra=valor_compra,
        percentual_cashback=configuracao.percentual_cashback,
        valor_cashback=valor_cashback,
        data_compra=hoje,
        data_liberacao=hoje + timedelta(days=configuracao.dias_liberacao),
        data_expiracao=hoje + timedelta(days=configuracao.dias_expiracao),
        status=LancamentoCashback.STATUS_PENDENTE,
        observacao=observacao
    )

    return lancamento