from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from fiscal.domain.selecao_fiscal import (
    ContextoSelecaoFiscal,
    EstadoSelecaoFiscal,
    ResultadoSelecaoFiscal,
)
from fiscal.services_motor_selecao import selecionar_regra


class StatusProdutoFiscal(StrEnum):
    VALIDA = "valida"
    INCOMPLETA = "incompleta"
    SEM_REGRA = "sem_regra"
    AMBIGUA = "ambigua"
    CONTEXTO_INVALIDO = "contexto_invalido"


@dataclass(frozen=True, slots=True)
class ProdutoFiscalResolvido:
    produto: Any
    origem: Any = None
    ncm: Any = None
    cest: Any = None
    cst_icms: Any = None
    csosn: Any = None
    cst_pis: Any = None
    cst_cofins: Any = None
    cst_ipi: Any = None
    beneficio: Any = None
    regra: Any = None
    observacoes: tuple[str, ...] = ()
    status: StatusProdutoFiscal = StatusProdutoFiscal.INCOMPLETA
    motivo_selecao: str = ""
    alertas: tuple[str, ...] = ()
    memoria_decisao: dict[str, Any] | None = None
    resultado_selecao_fiscal: ResultadoSelecaoFiscal | None = None

    @property
    def valido(self) -> bool:
        return self.status == StatusProdutoFiscal.VALIDA


def _preenchido(valor: Any) -> bool:
    if valor is None:
        return False

    if isinstance(valor, str):
        return bool(valor.strip())

    return True


def _primeiro_preenchido(*valores: Any) -> Any:
    for valor in valores:
        if _preenchido(valor):
            return valor

    return None


def _contexto_com_classificacao_produto(
    *,
    contexto: ContextoSelecaoFiscal,
    produto: Any,
) -> ContextoSelecaoFiscal:
    ncm_produto = getattr(produto, "ncm_fiscal", None)
    cest_produto = getattr(produto, "cest", None)

    return ContextoSelecaoFiscal(
        data_operacao=contexto.data_operacao,
        regime_tributario=contexto.regime_tributario,
        tipo_operacao=contexto.tipo_operacao,
        finalidade_operacao=contexto.finalidade_operacao,
        uf_origem=contexto.uf_origem,
        uf_destino=contexto.uf_destino,
        matriz=contexto.matriz,
        loja=contexto.loja,
        contribuinte_icms=contexto.contribuinte_icms,
        consumidor_final=contexto.consumidor_final,
        ncm=ncm_produto or contexto.ncm,
        cest=cest_produto or contexto.cest,
    )


def _resolver_regra(
    *,
    produto: Any,
    contexto: ContextoSelecaoFiscal,
) -> tuple[Any, Any, str]:
    regra_direta = getattr(produto, "regra_fiscal_padrao", None)

    if regra_direta is not None:
        return (
            regra_direta,
            None,
            "Regra fiscal vinculada diretamente ao produto.",
        )

    resultado = selecionar_regra(
        _contexto_com_classificacao_produto(
            contexto=contexto,
            produto=produto,
        )
    )

    if (
        resultado.estado == EstadoSelecaoFiscal.SELECIONADA
        and resultado.regra is not None
    ):
        return (
            resultado.regra,
            resultado,
            "Regra fiscal selecionada pelo Motor de Selecao.",
        )

    return None, resultado, "Nenhuma regra fiscal efetiva foi selecionada."


def _status_sem_regra(resultado: Any) -> StatusProdutoFiscal:
    if resultado is None:
        return StatusProdutoFiscal.SEM_REGRA

    if resultado.estado == EstadoSelecaoFiscal.AMBIGUA:
        return StatusProdutoFiscal.AMBIGUA

    if resultado.estado == EstadoSelecaoFiscal.CONTEXTO_INVALIDO:
        return StatusProdutoFiscal.CONTEXTO_INVALIDO

    return StatusProdutoFiscal.SEM_REGRA


def _observacoes_regra(regra: Any) -> tuple[str, ...]:
    if regra is None:
        return ()

    observacoes = getattr(regra, "observacoes", None)

    if not _preenchido(observacoes):
        return ()

    return (str(observacoes).strip(),)


def resolver_produto_fiscal(
    *,
    produto: Any,
    contexto: ContextoSelecaoFiscal,
) -> ProdutoFiscalResolvido:
    regra, resultado, motivo = _resolver_regra(
        produto=produto,
        contexto=contexto,
    )

    if regra is not None and resultado is None:
        resultado = ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.SELECIONADA,
            regra=regra,
            codigo_regra=str(
                getattr(regra, "codigo_interno", "") or ""
            ),
            prioridade=getattr(regra, "prioridade", None),
            criterios_atendidos=("regra_fiscal_padrao",),
            candidatas_avaliadas=1,
            memoria_decisao={
                "origem": "regra_fiscal_padrao",
                "codigo_regra": str(
                    getattr(regra, "codigo_interno", "") or ""
                ),
            },
        )

    ncm_produto = getattr(produto, "ncm_fiscal", None)
    ncm_legado = getattr(produto, "ncm", None)

    origem = getattr(produto, "origem_mercadoria", None)
    ncm = _primeiro_preenchido(
        ncm_produto,
        ncm_legado,
        getattr(regra, "ncm", None),
    )
    cest = _primeiro_preenchido(
        getattr(produto, "cest", None),
        getattr(regra, "cest", None),
    )
    cst_icms = _primeiro_preenchido(
        getattr(produto, "cst_icms", None),
        getattr(regra, "cst_icms", None),
    )
    csosn = _primeiro_preenchido(
        getattr(produto, "csosn", None),
        getattr(regra, "csosn", None),
    )
    cst_pis = _primeiro_preenchido(
        getattr(produto, "cst_pis", None),
        getattr(regra, "cst_pis", None),
    )
    cst_cofins = _primeiro_preenchido(
        getattr(produto, "cst_cofins", None),
        getattr(regra, "cst_cofins", None),
    )
    cst_ipi = _primeiro_preenchido(
        getattr(produto, "cst_ipi", None),
        getattr(regra, "cst_ipi", None),
    )
    beneficio = _primeiro_preenchido(
        getattr(produto, "beneficio_fiscal", None),
        getattr(regra, "beneficio_fiscal", None),
    )

    alertas: list[str] = []

    if contexto.regime_tributario == "simples":
        if cst_icms is not None:
            alertas.append(
                "CST ICMS foi ignorado porque o regime informado e Simples Nacional."
            )
        cst_icms = None

        if csosn is None:
            alertas.append(
                "O regime Simples Nacional exige uma classificacao CSOSN."
            )
    else:
        if csosn is not None:
            alertas.append(
                "CSOSN foi ignorado porque o regime informado nao e Simples Nacional."
            )
        csosn = None

        if cst_icms is None:
            alertas.append(
                "O regime informado exige uma classificacao CST ICMS."
            )

    if origem is None:
        alertas.append("Origem da mercadoria nao informada.")

    if ncm is None:
        alertas.append("NCM nao informado.")

    memoria = None
    observacoes = _observacoes_regra(regra)

    if resultado is not None:
        memoria = resultado.memoria_decisao

        for aviso in getattr(resultado, "avisos", ()) or ():
            alertas.append(str(aviso))

        conflitos = getattr(resultado, "regras_conflitantes", ()) or ()

        if conflitos:
            alertas.append(
                "Regras fiscais conflitantes: {0}.".format(
                    ", ".join(conflitos)
                )
            )

    if regra is None:
        status = _status_sem_regra(resultado)
    elif alertas:
        status = StatusProdutoFiscal.INCOMPLETA
    else:
        status = StatusProdutoFiscal.VALIDA

    return ProdutoFiscalResolvido(
        produto=produto,
        origem=origem,
        ncm=ncm,
        cest=cest,
        cst_icms=cst_icms,
        csosn=csosn,
        cst_pis=cst_pis,
        cst_cofins=cst_cofins,
        cst_ipi=cst_ipi,
        beneficio=beneficio,
        regra=regra,
        observacoes=observacoes,
        status=status,
        motivo_selecao=motivo,
        alertas=tuple(alertas),
        memoria_decisao=memoria,
        resultado_selecao_fiscal=resultado,
    )