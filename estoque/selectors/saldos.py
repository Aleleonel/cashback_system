"""Posicao de estoque por produto e loja, com reservas ativas."""
from decimal import Decimal
from django.db.models import Sum
from estoque.models import SaldoEstoque, ReservaEstoque
from estoque.choices import StatusReservaEstoque


def get_posicao_estoque(*, matriz, lojas, busca='', loja_id=None):
    qs = (SaldoEstoque.objects.filter(matriz=matriz, loja__in=lojas, produto__controla_estoque=True)
          .select_related('produto', 'loja').order_by('produto__nome', 'loja__nome', 'pk'))
    if busca:
        from django.db.models import Q
        qs = qs.filter(Q(produto__nome__icontains=busca) | Q(produto__codigo_interno__icontains=busca))
    if loja_id is not None:
        qs = qs.filter(loja_id=loja_id)
    return qs


def enriquecer_posicao_com_reservas(saldos, *, matriz):
    """Uma consulta agregada de reservas para a pagina atual."""
    saldos = list(saldos)
    if not saldos:
        return saldos
    lojas = {s.loja_id for s in saldos}
    produtos = {s.produto_id for s in saldos}
    rows = (ReservaEstoque.objects.filter(matriz=matriz, loja_id__in=lojas,
                produto_id__in=produtos, status=StatusReservaEstoque.ATIVA)
            .values('loja_id', 'produto_id').annotate(total=Sum('quantidade')))
    reservas = {(r['loja_id'], r['produto_id']): r['total'] for r in rows}
    for saldo in saldos:
        saldo.quantidade_reservada = reservas.get((saldo.loja_id, saldo.produto_id), Decimal('0.000'))
        saldo.quantidade_disponivel = saldo.quantidade_atual - saldo.quantidade_reservada
    return saldos
