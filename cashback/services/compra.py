from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from clientes.models import Cliente
from core.services import garantir_configuracao_sistema
from cashback.models import LancamentoCashback
from cashback.selectors import get_saldo_disponivel_cliente

from .cashback import usar_cashback


def calcular_cashback(*, valor_compra, percentual):
    valor_compra = Decimal(valor_compra)
    percentual = Decimal(percentual)

    return (valor_compra * percentual / Decimal('100')).quantize(
        Decimal('0.01')
    )


@transaction.atomic
def registrar_compra(
    *,
    matriz,
    loja,
    chave_idempotencia,
    cpf,
    nome,
    valor_compra,
    valor_base_cashback=None,
    valor_cashback_usado=0,
    telefone='',
    email='',
    data_nascimento=None,
    aceita_email=True,
    aceita_sms=False,
    observacao='',
):

    configuracao = garantir_configuracao_sistema(
        matriz=matriz
    )

    valor_compra = Decimal(valor_compra)
    valor_cashback_usado = Decimal(valor_cashback_usado or 0)

    if valor_base_cashback is None:
        valor_base_cashback = valor_compra

    valor_base_cashback = Decimal(valor_base_cashback)

    if valor_base_cashback < Decimal('0.00'):
        raise ValidationError(
            'A base de cálculo do cashback não pode ser negativa.'
        )

    if valor_base_cashback > valor_compra:
        raise ValidationError(
            'A base de cálculo do cashback não pode ser maior que o valor da compra.'
        )

    if valor_compra < configuracao.valor_minimo_compra:
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
        raise ValidationError(
            'Cliente inativo. Não é possível lançar cashback.'
        )

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

        if cliente.aceita_email != aceita_email:
            cliente.aceita_email = aceita_email
            campos_atualizar.append('aceita_email')

        if cliente.aceita_sms != aceita_sms:
            cliente.aceita_sms = aceita_sms
            campos_atualizar.append('aceita_sms')

        if campos_atualizar:
            cliente.save(update_fields=campos_atualizar)

    if valor_cashback_usado > 0:

        saldo_disponivel = get_saldo_disponivel_cliente(
            matriz=matriz,
            cliente=cliente
        )

        if valor_cashback_usado > saldo_disponivel:
            raise ValidationError(
                'O valor informado é maior que o saldo disponível.'
            )

        if valor_cashback_usado > valor_compra:
            raise ValidationError(
                'O cashback utilizado não pode ser maior que o valor da compra.'
            )

        usar_cashback(
            matriz=matriz,
            loja=loja,
            cliente=cliente,
            valor_usado=valor_cashback_usado,
            observacao='Uso de cashback na compra atual.'
        )

    hoje = timezone.localdate()

    valor_cashback = calcular_cashback(
        valor_compra=valor_base_cashback,
        percentual=configuracao.percentual_cashback
    )

    lancamento = LancamentoCashback.objects.create(
        matriz=matriz,
        loja=loja,
        chave_idempotencia=chave_idempotencia,
        cliente=cliente,
        valor_compra=valor_compra,
        valor_base_cashback=valor_base_cashback,
        percentual_cashback=configuracao.percentual_cashback,
        valor_cashback=valor_cashback,
        valor_utilizado=Decimal('0.00'),
        data_compra=hoje,
        data_liberacao=hoje + timedelta(days=configuracao.dias_liberacao),
        data_expiracao=hoje + timedelta(days=configuracao.dias_expiracao),
        observacao=observacao
    )

    return lancamento