from django.db import models

from .models import Cliente
from .utils import limpar_numero, normalizar_texto


def get_cliente_por_cpf(*, matriz, cpf):
    cpf_normalizado = limpar_numero(cpf)

    return Cliente.objects.filter(
        matriz=matriz,
        cpf_normalizado=cpf_normalizado,
        ativo=True
    ).select_related(
        'matriz',
        'loja_cadastro'
    ).first()


def get_clientes_da_matriz(*, matriz):
    return Cliente.objects.filter(
        matriz=matriz,
        ativo=True
    ).select_related(
        'matriz',
        'loja_cadastro'
    ).order_by('nome')


def aplicar_busca_clientes(queryset, busca):
    busca = (busca or '').strip()

    if not busca:
        return queryset

    busca_numerica = limpar_numero(busca)
    busca_texto = normalizar_texto(busca)

    filtros = (
        models.Q(nome__icontains=busca) |
        models.Q(email__icontains=busca) |
        models.Q(nome_normalizado__icontains=busca_texto) |
        models.Q(email_normalizado__icontains=busca_texto) |
        models.Q(razao_social__icontains=busca) |
        models.Q(nome_fantasia__icontains=busca)
    )

    if busca_numerica:
        filtros = filtros | (
            models.Q(cpf__icontains=busca) |
            models.Q(telefone__icontains=busca) |
            models.Q(cpf_normalizado__icontains=busca_numerica) |
            models.Q(cnpj_normalizado__icontains=busca_numerica) |
            models.Q(telefone_normalizado__icontains=busca_numerica)
        )

    return queryset.filter(filtros)

def obter_cliente_360(cliente):
    """Retorna métricas e histórico de vendas finalizadas do cliente em sua matriz."""
    from decimal import Decimal
    from django.db.models import Count, Sum, Max
    from pdv.models import Venda

    vendas = (
        Venda.objects
        .filter(
            cliente=cliente,
            matriz=cliente.matriz,
            status="finalizada",
        )
        .select_related("loja")
        .order_by("-finalizada_em", "-id")
    )

    agregados = vendas.aggregate(
        quantidade_compras=Count("id"),
        total_gasto=Sum("total"),
        ultima_compra=Max("finalizada_em"),
    )
    quantidade = agregados["quantidade_compras"] or 0
    total = agregados["total_gasto"] or Decimal("0")
    ticket = (total / quantidade) if quantidade else Decimal("0")

    from cashback.selectors import (
        get_movimentacoes_cliente,
        get_resumo_extrato_cliente,
        get_saldo_disponivel_cliente,
    )
    from vouchers.selectors import get_usos_voucher, get_vouchers_cliente

    matriz = cliente.matriz

    cashback = {
        "saldo_disponivel": get_saldo_disponivel_cliente(
            matriz=matriz,
            cliente=cliente,
        ),
        "movimentacoes": get_movimentacoes_cliente(
            matriz=matriz,
            cliente=cliente,
        ),
        "resumo": get_resumo_extrato_cliente(
            matriz=matriz,
            cliente=cliente,
        ),
    }

    vouchers = {
        "lista": get_vouchers_cliente(
            matriz=matriz,
            cliente=cliente,
        ),
        "usos": get_usos_voucher(
            matriz=matriz,
            cliente=cliente,
        ),
    }

    return {
        "total_gasto": total,
        "quantidade_compras": quantidade,
        "ticket_medio": ticket,
        "ultima_compra": agregados["ultima_compra"],
        "historico_vendas": vendas,
        "cashback": cashback,
        "vouchers": vouchers,
    }
