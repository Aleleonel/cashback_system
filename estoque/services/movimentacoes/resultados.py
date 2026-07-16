from dataclasses import dataclass

from estoque.models import MovimentacaoEstoque, SaldoEstoque


@dataclass(frozen=True)
class ResultadoMovimentacaoEstoque:
    saldo: SaldoEstoque
    movimentacao: MovimentacaoEstoque
    duplicada: bool = False
