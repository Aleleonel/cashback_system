"""Consultas relacionadas às movimentações de estoque."""

from django.db.models import Q

from estoque.models import MovimentacaoEstoque


def get_movimentacoes(*, matriz, busca=''):
    """Retorna as movimentações pertencentes à matriz informada."""
    movimentacoes = (
        MovimentacaoEstoque.objects
        .filter(matriz=matriz)
        .select_related(
            'produto',
            'loja',
            'usuario',
        )
        .order_by(
            '-criado_em',
            '-id',
        )
    )

    busca = busca.strip()

    if busca:
        movimentacoes = movimentacoes.filter(
            Q(produto__nome__icontains=busca)
            | Q(produto__codigo_interno__icontains=busca)
            | Q(documento_referencia__icontains=busca)
            | Q(origem_id__icontains=busca)
        )

    return movimentacoes
