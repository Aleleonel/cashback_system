from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from django.core.exceptions import ValidationError

from fiscal.domain import (
    EstadoSelecaoFiscal,
    ResultadoSelecaoFiscal,
)


ZERO = Decimal("0")


class EstadoCalculoTributario(StrEnum):
    CALCULADO = "calculado"
    REGRA_NAO_ENCONTRADA = "regra_nao_encontrada"
    REGRA_AMBIGUA = "regra_ambigua"
    CONTEXTO_INVALIDO = "contexto_invalido"
    PARAMETROS_INCOMPLETOS = "parametros_incompletos"


@dataclass(frozen=True, slots=True)
class ContextoCalculoTributario:
    resultado_selecao_fiscal: ResultadoSelecaoFiscal
    valor_produtos: Decimal
    quantidade: Decimal = Decimal("1")
    desconto: Decimal = ZERO
    acrescimo: Decimal = ZERO
    frete: Decimal = ZERO
    seguro: Decimal = ZERO
    outras_despesas: Decimal = ZERO
    valor_unitario: Decimal | None = None
    valor_item: Decimal | None = None
    base_manual: Decimal | None = None
    percentual_reducao_manual: Decimal | None = None
    informacoes_adicionais: dict[str, Any] = field(
        default_factory=dict
    )

    def validar(self):
        erros = {}

        valores = {
            "valor_produtos": self.valor_produtos,
            "quantidade": self.quantidade,
            "desconto": self.desconto,
            "acrescimo": self.acrescimo,
            "frete": self.frete,
            "seguro": self.seguro,
            "outras_despesas": self.outras_despesas,
            "valor_unitario": self.valor_unitario,
            "valor_item": self.valor_item,
            "base_manual": self.base_manual,
            "percentual_reducao_manual": (
                self.percentual_reducao_manual
            ),
        }

        for campo, valor in valores.items():
            if valor is None:
                continue

            if isinstance(valor, float):
                erros[campo] = (
                    "Utilize Decimal; valores float nao sao aceitos."
                )
                continue

            if not isinstance(valor, Decimal):
                erros[campo] = (
                    "O valor deve ser informado como Decimal."
                )
                continue

            if valor < ZERO:
                erros[campo] = (
                    "O valor nao pode ser negativo."
                )

        if self.quantidade == ZERO:
            erros["quantidade"] = (
                "A quantidade deve ser maior que zero."
            )

        if (
            self.percentual_reducao_manual is not None
            and self.percentual_reducao_manual
            > Decimal("100")
        ):
            erros["percentual_reducao_manual"] = (
                "O percentual deve estar entre zero e cem."
            )

        if not isinstance(
            self.resultado_selecao_fiscal,
            ResultadoSelecaoFiscal,
        ):
            erros["resultado_selecao_fiscal"] = (
                "Informe um resultado de selecao fiscal valido."
            )

        if erros:
            raise ValidationError(erros)

        return self


@dataclass(frozen=True, slots=True)
class ResultadoCalculoTributario:
    estado: EstadoCalculoTributario
    regra: Any = None
    base_operacao: Decimal = ZERO
    base_icms: Decimal = ZERO
    valor_icms_bruto: Decimal = ZERO
    valor_icms_diferido: Decimal = ZERO
    valor_icms: Decimal = ZERO
    base_fcp: Decimal = ZERO
    valor_fcp: Decimal = ZERO
    base_pis: Decimal = ZERO
    valor_pis: Decimal = ZERO
    base_cofins: Decimal = ZERO
    valor_cofins: Decimal = ZERO
    base_ipi: Decimal = ZERO
    valor_ipi: Decimal = ZERO
    valor_total_tributos: Decimal = ZERO
    memoria_calculo: dict[str, Any] = field(
        default_factory=dict
    )
    avisos: tuple[str, ...] = ()
    erros: tuple[str, ...] = ()

    @property
    def calculado(self):
        return (
            self.estado
            == EstadoCalculoTributario.CALCULADO
        )
