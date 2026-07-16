from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from estoque.models import MovimentacaoEstoque, SaldoEstoque

if TYPE_CHECKING:
    from estoque.models import ReservaEstoque


@dataclass(frozen=True)
class ResultadoMovimentacaoEstoque:
    saldo: SaldoEstoque
    movimentacao: MovimentacaoEstoque
    duplicada: bool = False


@dataclass(frozen=True)
class ResultadoTransferenciaEstoque:
    grupo_transferencia: UUID
    origem: ResultadoMovimentacaoEstoque
    destino: ResultadoMovimentacaoEstoque

    @property
    def duplicada(self):
        return (
            self.origem.duplicada
            and self.destino.duplicada
        )


@dataclass(frozen=True)
class ResultadoReservaEstoque:
    reserva: ReservaEstoque
    duplicada: bool = False