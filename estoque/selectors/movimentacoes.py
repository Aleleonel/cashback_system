"""Consultas relacionadas às movimentações de estoque."""

from estoque.models import MovimentacaoEstoque


def get_movimentacoes(*, matriz, busca=''):
    """
    Retorna a base de movimentações da matriz.

    A busca e os campos exibidos serão ampliados em uma etapa posterior,
    depois da validação funcional da primeira tela.
    """
    del busca

    return MovimentacaoEstoque.objects.filter(
        matriz=matriz
    ).none()