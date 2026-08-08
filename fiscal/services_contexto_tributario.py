from datetime import date

from django.core.exceptions import ValidationError

from fiscal.domain import ContextoSelecaoFiscal
from fiscal.models_regra_fiscal import RegraFiscal, UFS_VALIDAS
from fiscal.selectors_configuracao_fiscal import (
    get_configuracao_fiscal_matriz,
)


def _resolver_booleano(*, valor_explicito, valor_padrao):
    if valor_explicito is not None:
        return valor_explicito

    return valor_padrao


def construir_contexto_tributario(
    *,
    matriz,
    loja=None,
    produto=None,
    data_operacao=None,
    tipo_operacao=RegraFiscal.TIPO_SAIDA,
    finalidade_operacao=RegraFiscal.FINALIDADE_VENDA,
    uf_destino,
    contribuinte_icms=None,
    consumidor_final=None,
):
    erros = {}

    if matriz is None:
        erros["matriz"] = "Informe a matriz da operacao."

    if (
        loja is not None
        and matriz is not None
        and getattr(loja, "matriz_id", None)
        != getattr(matriz, "id", None)
    ):
        erros["loja"] = "A loja nao pertence a matriz informada."

    configuracao = None

    if matriz is not None:
        configuracao = get_configuracao_fiscal_matriz(
            matriz=matriz,
        )

    if configuracao is None:
        erros["configuracao_fiscal"] = (
            "A matriz nao possui configuracao fiscal ativa."
        )
    elif not configuracao.pronta_para_operacao:
        erros["configuracao_fiscal"] = (
            "A configuracao fiscal da matriz esta incompleta."
        )

    uf_destino_normalizada = RegraFiscal.normalizar_uf(
        uf_destino
    )

    if not uf_destino_normalizada:
        erros["uf_destino"] = "Informe a UF de destino."
    elif uf_destino_normalizada not in UFS_VALIDAS:
        erros["uf_destino"] = "Informe uma UF brasileira valida."

    if erros:
        raise ValidationError(erros)

    contexto = ContextoSelecaoFiscal(
        data_operacao=data_operacao or date.today(),
        regime_tributario=configuracao.regime_tributario,
        tipo_operacao=tipo_operacao,
        finalidade_operacao=finalidade_operacao,
        uf_origem=configuracao.uf_origem,
        uf_destino=uf_destino_normalizada,
        matriz=matriz,
        loja=loja,
        contribuinte_icms=_resolver_booleano(
            valor_explicito=contribuinte_icms,
            valor_padrao=configuracao.contribuinte_icms,
        ),
        consumidor_final=_resolver_booleano(
            valor_explicito=consumidor_final,
            valor_padrao=configuracao.consumidor_final_padrao,
        ),
        ncm=getattr(produto, "ncm", None),
        cest=getattr(produto, "cest", None),
    ).normalizado()

    return contexto.validar()
