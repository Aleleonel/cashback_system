from dataclasses import dataclass
from uuid import UUID

from estoque.models import MovimentacaoEstoque, SaldoEstoque


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
