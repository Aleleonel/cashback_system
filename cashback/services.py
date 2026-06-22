from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from clientes.models import Cliente
from core.models import ConfiguracaoSistema

from .models import (
    LancamentoCashback,
    UsoCashback,
    UsoLancamentoCashback,
)
from .selectors import get_lancamentos_disponiveis_cliente


def calcular_cashback(*, valor_compra, percentual):
    valor_compra = Decimal(valor_compra)
    percentual = Decimal(percentual)

    return (valor_compra * percentual / Decimal('100')).quantize(
        Decimal('0.01')
    )


@transaction.atomic
def registrar_compra(*, matriz, loja, cpf, nome, valor_compra,
                     telefone='', email='', data_nascimento=None,
                     aceita_email=True, aceita_sms=False, observacao=''):

    configuracao = ConfiguracaoSistema.objects.select_for_update().get(
        matriz=matriz
    )

    if Decimal(valor_compra) < configuracao.valor_minimo_compra:
        raise ValidationError(
            'Valor da compra abaixo do mínimo configurado para gerar cashback.'
        )

    cliente, criado = Cliente.objects.get_or_create(
        matriz=matriz,
        cpf=cpf,
        defaults={
            'loja_cadastro': loja,
            'nome': nome,
            'telefone': telefone,
            'email': email,
            'data_nascimento': data_nascimento,
            'aceita_email': aceita_email,
            'aceita_sms': aceita_sms,
        }
    )

    if not cliente.ativo:
        raise ValidationError('Cliente inativo. Não é possível lançar cashback.')

    if not criado:
        campos_atualizar = []

        if nome and cliente.nome != nome:
            cliente.nome = nome
            campos_atualizar.append('nome')

        if telefone and cliente.telefone != telefone:
            cliente.telefone = telefone
            campos_atualizar.append('telefone')

        if email and cliente.email != email:
            cliente.email = email
            campos_atualizar.append('email')

        if data_nascimento and cliente.data_nascimento != data_nascimento:
            cliente.data_nascimento = data_nascimento
            campos_atualizar.append('data_nascimento')

        if campos_atualizar:
            campos_atualizar.append('atualizado_em')
            cliente.save(update_fields=campos_atualizar)

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
        valor_utilizado=Decimal('0.00'),
        data_compra=hoje,
        data_liberacao=hoje + timedelta(days=configuracao.dias_liberacao),
        data_expiracao=hoje + timedelta(days=configuracao.dias_expiracao),
        observacao=observacao
    )

    return lancamento


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