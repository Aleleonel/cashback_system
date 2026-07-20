"""Views do módulo de estoque."""

from .movimentacoes import (
    criar_entrada_estoque,
    lista_movimentacoes,
)

__all__ = [
    'lista_movimentacoes',
]