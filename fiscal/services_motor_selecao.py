from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import Q

from fiscal.domain import (
    ContextoSelecaoFiscal,
    EstadoSelecaoFiscal,
    ResultadoSelecaoFiscal,
)
from fiscal.models import RegraFiscal
from fiscal.selectors_regra_fiscal import get_regras_ativas_vigentes


class RegraFiscalAmbiguaError(Exception):
    pass


PESOS_ESPECIFICIDADE = {
    "loja": 64,
    "matriz": 32,
    "ncm": 16,
    "cest": 16,
    "cfop": 12,
    "uf_origem": 8,
    "uf_destino": 8,
    "regime_tributario": 6,
    "tipo_operacao": 4,
    "contribuinte_icms": 2,
    "consumidor_final": 2,
}


def _pontuar_regra(regra):
    criterios = {
        "loja": regra.loja_id is not None,
        "matriz": regra.matriz_id is not None,
        "ncm": regra.ncm_id is not None,
        "cest": regra.cest_id is not None,
        "cfop": regra.cfop_id is not None,
        "uf_origem": bool(regra.uf_origem),
        "uf_destino": bool(regra.uf_destino),
        "regime_tributario": (
            regra.regime_tributario != RegraFiscal.REGIME_TODOS
        ),
        "tipo_operacao": regra.tipo_operacao != RegraFiscal.TIPO_AMBOS,
        "contribuinte_icms": regra.contribuinte_icms is not None,
        "consumidor_final": regra.consumidor_final is not None,
    }

    pontuacao = sum(
        PESOS_ESPECIFICIDADE[nome]
        for nome, ativo in criterios.items()
        if ativo
    )
    atendidos = tuple(nome for nome, ativo in criterios.items() if ativo)
    coringas = tuple(nome for nome, ativo in criterios.items() if not ativo)
    return pontuacao, atendidos, coringas


def _registrar_etapa(memoria, etapa, queryset):
    quantidade = queryset.count()
    memoria["etapas"].append(
        {"etapa": etapa, "quantidade": quantidade}
    )
    return queryset


def _filtrar_candidatas(contexto):
    regras = get_regras_ativas_vigentes(
        data_operacao=contexto.data_operacao
    )

    memoria = {
        "contexto": {
            "data_operacao": contexto.data_operacao.isoformat(),
            "regime_tributario": contexto.regime_tributario,
            "tipo_operacao": contexto.tipo_operacao,
            "finalidade_operacao": contexto.finalidade_operacao,
            "uf_origem": contexto.uf_origem,
            "uf_destino": contexto.uf_destino,
            "matriz_id": getattr(contexto.matriz, "id", None),
            "loja_id": getattr(contexto.loja, "id", None),
            "ncm_id": getattr(contexto.ncm, "id", None),
            "cest_id": getattr(contexto.cest, "id", None),
            "cfop_id": getattr(contexto.cfop, "id", None),
        },
        "etapas": [],
    }

    _registrar_etapa(memoria, "ativas_e_vigentes", regras)

    regras = regras.filter(
        Q(matriz__isnull=True) | Q(matriz=contexto.matriz),
        Q(loja__isnull=True) | Q(loja=contexto.loja),
    )
    _registrar_etapa(memoria, "escopo", regras)

    regras = regras.filter(
        Q(regime_tributario=RegraFiscal.REGIME_TODOS)
        | Q(regime_tributario=contexto.regime_tributario),
        Q(tipo_operacao=RegraFiscal.TIPO_AMBOS)
        | Q(tipo_operacao=contexto.tipo_operacao),
        finalidade_operacao=contexto.finalidade_operacao,
    )
    _registrar_etapa(memoria, "regime_e_operacao", regras)

    regras = regras.filter(
        Q(uf_origem="") | Q(uf_origem=contexto.uf_origem),
        Q(uf_destino="") | Q(uf_destino=contexto.uf_destino),
        Q(contribuinte_icms__isnull=True)
        | Q(contribuinte_icms=contexto.contribuinte_icms),
        Q(consumidor_final__isnull=True)
        | Q(consumidor_final=contexto.consumidor_final),
    )
    _registrar_etapa(memoria, "destinatario_e_ufs", regras)

    regras = regras.filter(
        Q(ncm__isnull=True) | Q(ncm=contexto.ncm),
        Q(cest__isnull=True) | Q(cest=contexto.cest),
        Q(cfop__isnull=True) | Q(cfop=contexto.cfop),
    )
    _registrar_etapa(memoria, "classificacao_fiscal", regras)

    candidatas = list(regras)
    memoria["candidatas"] = [
        regra.codigo_interno for regra in candidatas
    ]
    return candidatas, memoria


def selecionar_regra(contexto: ContextoSelecaoFiscal):
    try:
        contexto = contexto.normalizado()
        contexto.validar()
    except ValidationError as erro:
        return ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.CONTEXTO_INVALIDO,
            avisos=tuple(erro.messages),
            memoria_decisao={
                "erro_contexto": (
                    erro.message_dict
                    if hasattr(erro, "message_dict")
                    else erro.messages
                )
            },
        )

    candidatas, memoria = _filtrar_candidatas(contexto)

    if not candidatas:
        memoria["resultado"] = "nao_encontrada"
        return ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.NAO_ENCONTRADA,
            candidatas_avaliadas=0,
            avisos=("Nenhuma regra fiscal atende ao contexto.",),
            memoria_decisao=memoria,
        )

    avaliadas = []
    for regra in candidatas:
        pontuacao, atendidos, coringas = _pontuar_regra(regra)
        avaliadas.append(
            {
                "regra": regra,
                "pontuacao": pontuacao,
                "atendidos": atendidos,
                "coringas": coringas,
            }
        )

    avaliadas.sort(
        key=lambda item: (
            item["regra"].prioridade,
            -item["pontuacao"],
            item["regra"].codigo_interno,
        )
    )

    melhor = avaliadas[0]
    empatadas = [
        item
        for item in avaliadas
        if (
            item["regra"].prioridade
            == melhor["regra"].prioridade
            and item["pontuacao"] == melhor["pontuacao"]
        )
    ]

    memoria["avaliacao"] = [
        {
            "codigo": item["regra"].codigo_interno,
            "prioridade": item["regra"].prioridade,
            "pontuacao": item["pontuacao"],
            "criterios_atendidos": list(item["atendidos"]),
            "criterios_coringa": list(item["coringas"]),
        }
        for item in avaliadas
    ]

    if len(empatadas) > 1:
        conflitos = tuple(
            item["regra"].codigo_interno for item in empatadas
        )
        memoria["resultado"] = "ambigua"
        memoria["regras_conflitantes"] = list(conflitos)
        return ResultadoSelecaoFiscal(
            estado=EstadoSelecaoFiscal.AMBIGUA,
            candidatas_avaliadas=len(candidatas),
            avisos=("Existem regras fiscais ambiguas.",),
            memoria_decisao=memoria,
            regras_conflitantes=conflitos,
        )

    regra = melhor["regra"]
    memoria.update(
        {
            "resultado": "selecionada",
            "regra_selecionada": regra.codigo_interno,
            "prioridade_vencedora": regra.prioridade,
            "pontuacao_vencedora": melhor["pontuacao"],
        }
    )

    return ResultadoSelecaoFiscal(
        estado=EstadoSelecaoFiscal.SELECIONADA,
        regra=regra,
        codigo_regra=regra.codigo_interno,
        prioridade=regra.prioridade,
        especificidade=melhor["pontuacao"],
        criterios_atendidos=melhor["atendidos"],
        criterios_coringa=melhor["coringas"],
        candidatas_avaliadas=len(candidatas),
        memoria_decisao=memoria,
    )


def selecionar_regra_fiscal(**contexto):
    contexto = dict(contexto)
    contexto.setdefault(
        "data_operacao",
        date.today(),
    )

    resultado = selecionar_regra(
        ContextoSelecaoFiscal(**contexto)
    )

    if resultado.estado == EstadoSelecaoFiscal.AMBIGUA:
        codigos = ", ".join(resultado.regras_conflitantes)
        raise RegraFiscalAmbiguaError(
            f"Regras fiscais ambiguas: {codigos}."
        )

    if not resultado.selecionada:
        return None

    return resultado.regra
