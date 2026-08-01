"""Views do módulo de estoque."""

from .movimentacoes import (
    criar_ajuste_estoque,
    criar_entrada_estoque,
    criar_saida_estoque,
    criar_transferencia_estoque,
    lista_movimentacoes,
)

__all__ = [
    'criar_ajuste_estoque',
    'criar_entrada_estoque',
    'criar_saida_estoque',
    'criar_transferencia_estoque',
    'lista_movimentacoes',
]