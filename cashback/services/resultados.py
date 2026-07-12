from dataclasses import dataclass
from typing import Any

from cashback.models import LancamentoCashback
from clientes.models import Cliente


@dataclass(frozen=True)
class ResultadoOperacaoVenda:
    compra: LancamentoCashback
    cliente: Cliente
    uso_voucher: Any = None
    beneficios: dict | None = None
    duplicada: bool = False