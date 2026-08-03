from decimal import (
    Decimal,
    ROUND_HALF_UP,
)

from django.core.exceptions import ValidationError

from fiscal.domain import (
    EstadoSelecaoFiscal,
)
from fiscal.domain.calculo_tributario import (
    ContextoCalculoTributario,
    EstadoCalculoTributario,
    ResultadoCalculoTributario,
)


ZERO = Decimal("0")
CEM = Decimal("100")
CASAS_MOEDA = Decimal("0.01")
CASAS_INTERMEDIARIAS = Decimal("0.00000001")


def quantizar_moeda(valor):
    return Decimal(valor).quantize(
        CASAS_MOEDA,
        rounding=ROUND_HALF_UP,
    )


def quantizar_intermediario(valor):
    return Decimal(valor).quantize(
        CASAS_INTERMEDIARIAS,
        rounding=ROUND_HALF_UP,
    )


def _calcular_percentual(base, aliquota):
    bruto = (
        quantizar_intermediario(base)
        * quantizar_intermediario(aliquota)
        / CEM
    )

    return {
        "bruto": bruto,
        "final": quantizar_moeda(bruto),
    }


def _resultado_bloqueado(contexto):
    selecao = contexto.resultado_selecao_fiscal

    if selecao.estado == EstadoSelecaoFiscal.NAO_ENCONTRADA:
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario
                .REGRA_NAO_ENCONTRADA
            ),
            avisos=(
                "O calculo foi bloqueado porque nenhuma regra fiscal foi encontrada.",
            ),
            memoria_calculo={
                "selecao_fiscal": selecao.memoria_decisao,
            },
        )

    if selecao.estado == EstadoSelecaoFiscal.AMBIGUA:
        return ResultadoCalculoTributario(
            estado=EstadoCalculoTributario.REGRA_AMBIGUA,
            avisos=(
                "O calculo foi bloqueado porque existem regras fiscais ambiguas.",
            ),
            memoria_calculo={
                "selecao_fiscal": selecao.memoria_decisao,
                "regras_conflitantes": list(
                    selecao.regras_conflitantes
                ),
            },
        )

    if (
        selecao.estado
        == EstadoSelecaoFiscal.CONTEXTO_INVALIDO
    ):
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario.CONTEXTO_INVALIDO
            ),
            erros=tuple(selecao.avisos),
            memoria_calculo={
                "selecao_fiscal": selecao.memoria_decisao,
            },
        )

    if not selecao.selecionada or selecao.regra is None:
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario.CONTEXTO_INVALIDO
            ),
            erros=(
                "Resultado de selecao fiscal invalido.",
            ),
        )

    return None


def _calcular_base_operacao(contexto):
    base = (
        contexto.valor_produtos
        - contexto.desconto
        + contexto.acrescimo
        + contexto.frete
        + contexto.seguro
        + contexto.outras_despesas
    )

    if contexto.base_manual is not None:
        base = contexto.base_manual

    return quantizar_intermediario(base)


def _resolver_reducao(contexto, regra, avisos):
    reducao_regra = regra.reducao_base_icms
    reducao_manual = contexto.percentual_reducao_manual

    if (
        reducao_manual is not None
        and reducao_regra is not None
        and reducao_manual != reducao_regra
    ):
        avisos.append(
            "A reducao manual substituiu a reducao configurada na regra fiscal."
        )

    if reducao_manual is not None:
        return reducao_manual

    return reducao_regra or ZERO


def calcular_tributos(
    contexto: ContextoCalculoTributario,
):
    try:
        contexto.validar()
    except ValidationError as erro:
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario.CONTEXTO_INVALIDO
            ),
            erros=tuple(erro.messages),
            memoria_calculo={
                "erro_contexto": (
                    erro.message_dict
                    if hasattr(erro, "message_dict")
                    else erro.messages
                )
            },
        )

    bloqueado = _resultado_bloqueado(contexto)
    if bloqueado is not None:
        return bloqueado

    regra = contexto.resultado_selecao_fiscal.regra
    avisos = []

    base_operacao = _calcular_base_operacao(contexto)

    if base_operacao < ZERO:
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario.CONTEXTO_INVALIDO
            ),
            erros=(
                "A base da operacao nao pode ser negativa.",
            ),
            memoria_calculo={
                "base_operacao_intermediaria": str(
                    base_operacao
                ),
            },
        )

    reducao = _resolver_reducao(
        contexto,
        regra,
        avisos,
    )

    if reducao < ZERO or reducao > CEM:
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario.CONTEXTO_INVALIDO
            ),
            erros=(
                "A reducao da base deve estar entre zero e cem.",
            ),
        )

    fator_reducao = (
        CEM - reducao
    ) / CEM

    base_icms_intermediaria = (
        base_operacao * fator_reducao
    )
    base_icms = quantizar_moeda(
        base_icms_intermediaria
    )

    parametros = {
        "icms": regra.aliquota_icms,
        "fcp": regra.aliquota_fcp,
        "pis": regra.aliquota_pis,
        "cofins": regra.aliquota_cofins,
        "ipi": regra.aliquota_ipi,
    }

    calculos = {}
    for nome, aliquota in parametros.items():
        if aliquota is None:
            calculos[nome] = {
                "calculado": False,
                "aliquota": None,
                "bruto": ZERO,
                "final": ZERO,
            }
            avisos.append(
                f"Aliquota de {nome.upper()} nao informada; tributo nao calculado."
            )
            continue

        base = (
            base_icms
            if nome in {"icms", "fcp"}
            else quantizar_moeda(base_operacao)
        )

        resultado = _calcular_percentual(
            base,
            aliquota,
        )
        calculos[nome] = {
            "calculado": True,
            "aliquota": aliquota,
            "bruto": resultado["bruto"],
            "final": resultado["final"],
        }

    valor_icms_bruto = calculos["icms"]["final"]

    percentual_diferimento = (
        regra.diferimento_icms or ZERO
    )
    if (
        percentual_diferimento < ZERO
        or percentual_diferimento > CEM
    ):
        return ResultadoCalculoTributario(
            estado=(
                EstadoCalculoTributario.CONTEXTO_INVALIDO
            ),
            erros=(
                "O diferimento deve estar entre zero e cem.",
            ),
        )

    diferimento = _calcular_percentual(
        valor_icms_bruto,
        percentual_diferimento,
    )
    valor_icms_diferido = diferimento["final"]
    valor_icms = quantizar_moeda(
        valor_icms_bruto
        - valor_icms_diferido
    )

    valores = {
        "icms": valor_icms,
        "fcp": calculos["fcp"]["final"],
        "pis": calculos["pis"]["final"],
        "cofins": calculos["cofins"]["final"],
        "ipi": calculos["ipi"]["final"],
    }

    total_tributos = quantizar_moeda(
        sum(
            valores.values(),
            ZERO,
        )
    )

    quantidade_calculada = sum(
        1
        for item in calculos.values()
        if item["calculado"]
    )

    estado = EstadoCalculoTributario.CALCULADO
    if quantidade_calculada == 0:
        estado = (
            EstadoCalculoTributario
            .PARAMETROS_INCOMPLETOS
        )

    memoria = {
        "regra": {
            "codigo": regra.codigo_interno,
            "prioridade": regra.prioridade,
            "beneficio_fiscal": (
                regra.beneficio_fiscal.codigo
                if regra.beneficio_fiscal_id
                else None
            ),
        },
        "selecao_fiscal": (
            contexto.resultado_selecao_fiscal
            .memoria_decisao
        ),
        "componentes_base": {
            "valor_produtos": str(
                contexto.valor_produtos
            ),
            "desconto": str(contexto.desconto),
            "acrescimo": str(contexto.acrescimo),
            "frete": str(contexto.frete),
            "seguro": str(contexto.seguro),
            "outras_despesas": str(
                contexto.outras_despesas
            ),
            "base_manual": (
                str(contexto.base_manual)
                if contexto.base_manual is not None
                else None
            ),
        },
        "base_operacao_intermediaria": str(
            base_operacao
        ),
        "base_operacao_final": str(
            quantizar_moeda(base_operacao)
        ),
        "reducao_base_icms": str(reducao),
        "base_icms_intermediaria": str(
            base_icms_intermediaria
        ),
        "base_icms_final": str(base_icms),
        "tributos": {
            nome: {
                "calculado": dados["calculado"],
                "aliquota": (
                    str(dados["aliquota"])
                    if dados["aliquota"] is not None
                    else None
                ),
                "valor_bruto": str(dados["bruto"]),
                "valor_final": str(dados["final"]),
            }
            for nome, dados in calculos.items()
        },
        "diferimento": {
            "percentual": str(
                percentual_diferimento
            ),
            "valor_icms_bruto": str(
                valor_icms_bruto
            ),
            "valor_diferido": str(
                valor_icms_diferido
            ),
            "valor_icms_devido": str(valor_icms),
        },
        "valor_total_tributos": str(
            total_tributos
        ),
        "avisos": list(avisos),
    }

    base_operacao_final = quantizar_moeda(
        base_operacao
    )

    return ResultadoCalculoTributario(
        estado=estado,
        regra=regra,
        base_operacao=base_operacao_final,
        base_icms=base_icms,
        valor_icms_bruto=valor_icms_bruto,
        valor_icms_diferido=valor_icms_diferido,
        valor_icms=valor_icms,
        base_fcp=base_icms,
        valor_fcp=valores["fcp"],
        base_pis=base_operacao_final,
        valor_pis=valores["pis"],
        base_cofins=base_operacao_final,
        valor_cofins=valores["cofins"],
        base_ipi=base_operacao_final,
        valor_ipi=valores["ipi"],
        valor_total_tributos=total_tributos,
        memoria_calculo=memoria,
        avisos=tuple(avisos),
    )
