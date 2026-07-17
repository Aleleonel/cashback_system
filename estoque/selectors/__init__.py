"""Selectors do modulo de estoque."""

from .reservas import (
    get_quantidade_reservada,
    get_saldo_disponivel,
)

__all__ = [
    'get_quantidade_reservada',
    'get_saldo_disponivel',
]
