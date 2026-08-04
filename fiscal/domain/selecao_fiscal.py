from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from django.core.exceptions import ValidationError

from fiscal.models import RegraFiscal


class EstadoSelecaoFiscal(StrEnum):
    SELECIONADA = "selecionada"
    NAO_ENCONTRADA = "nao_encontrada"
    AMBIGUA = "ambigua"
    CONTEXTO_INVALIDO = "contexto_invalido"


@dataclass(frozen=True, slots=True)
class ContextoSelecaoFiscal:
    data_operacao: date
    regime_tributario: str
    tipo_operacao: str
    finalidade_operacao: str
    uf_origem: str
    uf_destino: str
    matriz: Any = None
    loja: Any = None
    contribuinte_icms: bool | None = None
    consumidor_final: bool | None = None
    ncm: Any = None
    cest: Any = None
    cfop: Any = None

    def normalizado(self):
        return ContextoSelecaoFiscal(
            data_operacao=self.data_operacao,
            regime_tributario=(self.regime_tributario or "").strip(),
            tipo_operacao=(self.tipo_operacao or "").strip(),
            finalidade_operacao=(self.finalidade_operacao or "").strip(),
            uf_origem=RegraFiscal.normalizar_uf(self.uf_origem),
            uf_destino=RegraFiscal.normalizar_uf(self.uf_destino),
            matriz=self.matriz,
            loja=self.loja,
            contribuinte_icms=self.contribuinte_icms,
            consumidor_final=self.consumidor_final,
            ncm=self.ncm,
            cest=self.cest,
            cfop=self.cfop,
        )

    def validar(self):
        erros = {}

        if not self.data_operacao:
            erros["data_operacao"] = "Informe a data da operacao."

        regimes = {
            valor
            for valor, _ in RegraFiscal.REGIME_TRIBUTARIO_CHOICES
            if valor != RegraFiscal.REGIME_TODOS
        }
        if self.regime_tributario not in regimes:
            erros["regime_tributario"] = (
                "Informe um regime tributario especifico."
            )

        tipos = {
            valor
            for valor, _ in RegraFiscal.TIPO_OPERACAO_CHOICES
            if valor != RegraFiscal.TIPO_AMBOS
        }
        if self.tipo_operacao not in tipos:
            erros["tipo_operacao"] = "Informe entrada ou saida."

        finalidades = {
            valor
            for valor, _ in RegraFiscal.FINALIDADE_OPERACAO_CHOICES
        }
        if self.finalidade_operacao not in finalidades:
            erros["finalidade_operacao"] = (
                "Informe uma finalidade valida."
            )

        for campo in ("uf_origem", "uf_destino"):
            if len(getattr(self, campo)) != 2:
                erros[campo] = "Informe uma UF com dois caracteres."

        if self.loja is not None:
            if self.matriz is None:
                erros["matriz"] = "Informe a matriz da loja."
            elif getattr(self.loja, "matriz_id", None) != getattr(
                self.matriz, "id", None
            ):
                erros["loja"] = "A loja nao pertence a matriz informada."

        if erros:
            raise ValidationError(erros)

        return self


@dataclass(frozen=True, slots=True)
class ResultadoSelecaoFiscal:
    estado: EstadoSelecaoFiscal
    regra: Any = None
    codigo_regra: str = ""
    prioridade: int | None = None
    especificidade: int | None = None
    criterios_atendidos: tuple[str, ...] = ()
    criterios_coringa: tuple[str, ...] = ()
    candidatas_avaliadas: int = 0
    avisos: tuple[str, ...] = ()
    memoria_decisao: dict[str, Any] = field(default_factory=dict)
    regras_conflitantes: tuple[str, ...] = ()

    @property
    def selecionada(self):
        return self.estado == EstadoSelecaoFiscal.SELECIONADA
