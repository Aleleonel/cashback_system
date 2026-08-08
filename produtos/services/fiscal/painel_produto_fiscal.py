from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from fiscal.services_contexto_tributario import construir_contexto_tributario
from produtos.services.fiscal.resolver_produto_fiscal import (
    StatusProdutoFiscal,
    resolver_produto_fiscal,
)


STATUS_CONTEXTO_INCOMPLETO = "contexto_incompleto"
STATUS_CONFIGURACAO_AUSENTE = "configuracao_fiscal_ausente"


@dataclass(frozen=True, slots=True)
class PainelFiscalProduto:
    status: str
    status_label: str
    uf_destino: str = ""
    regime_tributario: str = ""
    uf_origem: str = ""
    regra: str = ""
    origem_regra: str = ""
    origem_mercadoria: str = ""
    ncm: str = ""
    cest: str = ""
    cst_icms: str = ""
    csosn: str = ""
    cst_pis: str = ""
    cst_cofins: str = ""
    cst_ipi: str = ""
    beneficio: str = ""
    observacoes: tuple[str, ...] = ()
    alertas: tuple[str, ...] = ()


def _texto(valor: Any) -> str:
    if valor is None:
        return ""

    for atributo in ("codigo", "sigla", "nome", "descricao"):
        conteudo = getattr(valor, atributo, None)
        if conteudo not in (None, ""):
            return str(conteudo).strip()

    return str(valor).strip()


def _status_label(status: str) -> str:
    labels = {
        StatusProdutoFiscal.VALIDA.value: "Configuracao valida",
        StatusProdutoFiscal.INCOMPLETA.value: "Configuracao incompleta",
        StatusProdutoFiscal.SEM_REGRA.value: "Sem regra fiscal",
        StatusProdutoFiscal.AMBIGUA.value: "Regras fiscais ambiguas",
        StatusProdutoFiscal.CONTEXTO_INVALIDO.value: "Contexto invalido",
        STATUS_CONTEXTO_INCOMPLETO: "Contexto incompleto",
        STATUS_CONFIGURACAO_AUSENTE: "Configuracao fiscal ausente",
    }
    return labels.get(status, status.replace("_", " ").title())


def _origem_regra(motivo: str) -> str:
    motivo_normalizado = (motivo or "").lower()

    if "diretamente ao produto" in motivo_normalizado:
        return "Regra vinculada ao Produto"

    if "motor de selecao" in motivo_normalizado:
        return "Regra selecionada pelo Motor"

    return ""


def _painel_sem_destino(produto) -> PainelFiscalProduto:
    return PainelFiscalProduto(
        status=STATUS_CONTEXTO_INCOMPLETO,
        status_label=_status_label(STATUS_CONTEXTO_INCOMPLETO),
        origem_mercadoria=_texto(
            getattr(produto, "origem_mercadoria", None)
        ),
        ncm=_texto(
            getattr(produto, "ncm_fiscal", None)
            or getattr(produto, "ncm", None)
        ),
        cest=_texto(getattr(produto, "cest", None)),
        alertas=(
            "Informe a UF de destino para visualizar a classificacao fiscal efetiva.",
        ),
    )


def montar_painel_fiscal_produto(
    *,
    produto,
    matriz,
    loja=None,
    uf_destino=None,
    data_operacao=None,
) -> PainelFiscalProduto:
    uf_destino = (uf_destino or "").strip().upper()

    if not uf_destino:
        return _painel_sem_destino(produto)

    try:
        contexto = construir_contexto_tributario(
            matriz=matriz,
            loja=loja,
            produto=produto,
            data_operacao=data_operacao,
            uf_destino=uf_destino,
        )
    except ObjectDoesNotExist:
        return PainelFiscalProduto(
            status=STATUS_CONFIGURACAO_AUSENTE,
            status_label=_status_label(STATUS_CONFIGURACAO_AUSENTE),
            uf_destino=uf_destino,
            alertas=(
                "A Matriz ainda nao possui configuracao fiscal ativa.",
            ),
        )
    except ValidationError as exc:
        mensagens = tuple(
            str(item)
            for item in getattr(exc, "messages", ())
        ) or (str(exc),)

        return PainelFiscalProduto(
            status=StatusProdutoFiscal.CONTEXTO_INVALIDO.value,
            status_label=_status_label(
                StatusProdutoFiscal.CONTEXTO_INVALIDO.value
            ),
            uf_destino=uf_destino,
            alertas=mensagens,
        )

    resolvido = resolver_produto_fiscal(
        produto=produto,
        contexto=contexto,
    )

    status = resolvido.status.value

    return PainelFiscalProduto(
        status=status,
        status_label=_status_label(status),
        uf_destino=_texto(contexto.uf_destino),
        regime_tributario=_texto(contexto.regime_tributario),
        uf_origem=_texto(contexto.uf_origem),
        regra=_texto(resolvido.regra),
        origem_regra=_origem_regra(resolvido.motivo_selecao),
        origem_mercadoria=_texto(resolvido.origem),
        ncm=_texto(resolvido.ncm),
        cest=_texto(resolvido.cest),
        cst_icms=_texto(resolvido.cst_icms),
        csosn=_texto(resolvido.csosn),
        cst_pis=_texto(resolvido.cst_pis),
        cst_cofins=_texto(resolvido.cst_cofins),
        cst_ipi=_texto(resolvido.cst_ipi),
        beneficio=_texto(resolvido.beneficio),
        observacoes=tuple(resolvido.observacoes),
        alertas=tuple(resolvido.alertas),
    )