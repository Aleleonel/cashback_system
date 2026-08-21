from dataclasses import asdict, dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from pdv.models import ItemVendaFiscal, VendaFiscal


ZERO = Decimal("0")


def _decimal_ou_none(valor):
    if valor is None or valor == "":
        return None
    return Decimal(str(valor))


def _decimal_ou_zero(valor):
    if valor is None or valor == "":
        return ZERO
    return Decimal(str(valor))


def _obter(objeto, nome, default=""):
    if objeto is None:
        return default
    return getattr(objeto, nome, default)


def _descricao(objeto):
    if objeto is None:
        return ""

    for campo in (
        "descricao",
        "nome",
        "titulo",
        "codigo",
        "codigo_interno",
    ):
        valor = getattr(objeto, campo, None)
        if valor:
            return str(valor)

    return str(objeto)


def _codigo(objeto):
    if objeto is None:
        return ""

    if isinstance(objeto, str):
        return objeto

    for campo in (
        "codigo",
        "codigo_interno",
        "ncm",
        "cest",
        "cfop",
    ):
        valor = getattr(objeto, campo, None)
        if valor:
            return str(valor)

    return ""


def _extrair_aliquota(resultado, nome):
    memoria = resultado.memoria_calculo or {}
    tributos = memoria.get("tributos") or {}
    dados = tributos.get(nome) or {}

    if "aliquota" in dados:
        return _decimal_ou_none(dados.get("aliquota"))

    regra = resultado.regra
    return _decimal_ou_none(
        getattr(regra, f"aliquota_{nome}", None)
        if regra is not None
        else None
    )


def _extrair_reducao(resultado):
    memoria = resultado.memoria_calculo or {}

    if "reducao_base_icms" in memoria:
        return _decimal_ou_zero(
            memoria.get("reducao_base_icms")
        )

    regra = resultado.regra
    return _decimal_ou_zero(
        getattr(regra, "reducao_base_icms", None)
        if regra is not None
        else None
    )


def _extrair_diferimento(resultado):
    memoria = resultado.memoria_calculo or {}
    diferimento = memoria.get("diferimento") or {}

    if "percentual" in diferimento:
        return _decimal_ou_zero(
            diferimento.get("percentual")
        )

    regra = resultado.regra
    return _decimal_ou_zero(
        getattr(regra, "diferimento_icms", None)
        if regra is not None
        else None
    )


def _validar_resultado_calculo(resultado):
    if resultado is None:
        raise ValidationError(
            "Informe o resultado do calculo tributario."
        )

    if not getattr(resultado, "calculado", False):
        raise ValidationError(
            "O calculo tributario nao esta apto "
            "para gerar snapshot fiscal."
        )

    if getattr(resultado, "erros", ()):
        raise ValidationError(
            "O calculo tributario possui erros "
            "e nao pode gerar snapshot fiscal."
        )

    if getattr(resultado, "regra", None) is None:
        raise ValidationError(
            "O resultado fiscal nao possui regra efetiva."
        )


@dataclass(frozen=True, slots=True)
class DadosItemVendaFiscal:
    regra_fiscal_id_original: int | None
    configuracao_fiscal_id_original: int | None

    origem_mercadoria_codigo: str
    ncm_codigo: str
    ncm_descricao: str
    cest_codigo: str
    cfop_codigo: str
    cfop_descricao: str

    cst_icms_codigo: str
    csosn_codigo: str
    cst_pis_codigo: str
    cst_cofins_codigo: str
    cst_ipi_codigo: str

    beneficio_fiscal_codigo: str
    beneficio_fiscal_descricao: str
    regra_fiscal_codigo: str
    regra_fiscal_descricao: str

    regime_tributario: str
    uf_origem: str
    uf_destino: str
    tipo_operacao: str
    finalidade_operacao: str
    contribuinte_icms: bool
    consumidor_final: bool

    quantidade: Decimal
    valor_unitario: Decimal
    valor_produtos: Decimal
    desconto: Decimal
    acrescimo: Decimal
    frete: Decimal
    seguro: Decimal
    outras_despesas: Decimal
    base_operacao: Decimal

    base_icms: Decimal
    aliquota_icms: Decimal | None
    percentual_reducao_base_icms: Decimal
    valor_icms_bruto: Decimal
    percentual_diferimento_icms: Decimal
    valor_icms_diferido: Decimal
    valor_icms: Decimal

    base_fcp: Decimal
    aliquota_fcp: Decimal | None
    valor_fcp: Decimal

    base_pis: Decimal
    aliquota_pis: Decimal | None
    valor_pis: Decimal

    base_cofins: Decimal
    aliquota_cofins: Decimal | None
    valor_cofins: Decimal

    base_ipi: Decimal
    aliquota_ipi: Decimal | None
    valor_ipi: Decimal

    valor_total_tributos: Decimal


@dataclass(frozen=True, slots=True)
class DadosVendaFiscal:
    configuracao_fiscal_id_original: int | None

    regime_tributario: str
    uf_origem: str
    uf_destino: str
    tipo_operacao: str
    finalidade_operacao: str
    contribuinte_icms: bool
    consumidor_final: bool

    total_base_operacao: Decimal
    total_base_icms: Decimal
    total_icms: Decimal
    total_fcp: Decimal
    total_base_pis: Decimal
    total_pis: Decimal
    total_base_cofins: Decimal
    total_cofins: Decimal
    total_base_ipi: Decimal
    total_ipi: Decimal
    total_tributos: Decimal


def construir_dados_item_venda_fiscal(
    *,
    item_venda,
    contexto_tributario,
    contexto_calculo,
    produto_fiscal,
    resultado_calculo,
    configuracao_fiscal_id_original=None,
):
    _validar_resultado_calculo(resultado_calculo)

    regra = resultado_calculo.regra

    ncm = _obter(produto_fiscal, "ncm")
    cest = _obter(produto_fiscal, "cest")
    beneficio = _obter(
        resultado_calculo.regra,
        "beneficio_fiscal",
        None,
    )

    origem = _obter(
        produto_fiscal,
        "origem",
        None,
    )

    if origem is None:
        origem = _obter(
            produto_fiscal,
            "origem_mercadoria",
            "",
        )

    cfop = _obter(regra, "cfop", "")

    return DadosItemVendaFiscal(
        regra_fiscal_id_original=getattr(
            regra,
            "pk",
            None,
        ),
        configuracao_fiscal_id_original=(
            configuracao_fiscal_id_original
        ),
        origem_mercadoria_codigo=str(
            _codigo(origem) or origem or ""
        ),
        ncm_codigo=str(_codigo(ncm)),
        ncm_descricao=_descricao(ncm),
        cest_codigo=str(_codigo(cest)),
        cfop_codigo=str(_codigo(cfop) or cfop or ""),
        cfop_descricao=_descricao(cfop),
        cst_icms_codigo=str(
            _codigo(_obter(regra, "cst_icms", "")) or ""
        ),
        csosn_codigo=str(
            _codigo(_obter(regra, "csosn", "")) or ""
        ),
        cst_pis_codigo=str(
            _codigo(_obter(regra, "cst_pis", "")) or ""
        ),
        cst_cofins_codigo=str(
            _codigo(_obter(regra, "cst_cofins", "")) or ""
        ),
        cst_ipi_codigo=str(
            _codigo(_obter(regra, "cst_ipi", "")) or ""
        ),
        beneficio_fiscal_codigo=str(
            _codigo(beneficio)
        ),
        beneficio_fiscal_descricao=_descricao(
            beneficio
        ),
        regra_fiscal_codigo=str(
            _obter(regra, "codigo_interno", "") or ""
        ),
        regra_fiscal_descricao=(
            _descricao(regra)
            or str(
                _obter(
                    regra,
                    "codigo_interno",
                    "",
                )
            )
        ),
        regime_tributario=str(
            _obter(
                contexto_tributario,
                "regime_tributario",
                "",
            )
        ),
        uf_origem=str(
            _obter(
                contexto_tributario,
                "uf_origem",
                "",
            )
        ),
        uf_destino=str(
            _obter(
                contexto_tributario,
                "uf_destino",
                "",
            )
        ),
        tipo_operacao=str(
            _obter(
                contexto_tributario,
                "tipo_operacao",
                "",
            )
        ),
        finalidade_operacao=str(
            _obter(
                contexto_tributario,
                "finalidade_operacao",
                "",
            )
        ),
        contribuinte_icms=bool(
            _obter(
                contexto_tributario,
                "contribuinte_icms",
                False,
            )
        ),
        consumidor_final=bool(
            _obter(
                contexto_tributario,
                "consumidor_final",
                True,
            )
        ),
        quantidade=Decimal(item_venda.quantidade),
        valor_unitario=Decimal(
            item_venda.preco_unitario
        ),
        valor_produtos=Decimal(
            item_venda.subtotal
        ),
        desconto=Decimal(item_venda.desconto),
        acrescimo=Decimal(item_venda.acrescimo),
        frete=_decimal_ou_zero(
            _obter(contexto_calculo, "frete", ZERO)
        ),
        seguro=_decimal_ou_zero(
            _obter(contexto_calculo, "seguro", ZERO)
        ),
        outras_despesas=_decimal_ou_zero(
            _obter(
                contexto_calculo,
                "outras_despesas",
                ZERO,
            )
        ),
        base_operacao=Decimal(
            resultado_calculo.base_operacao
        ),
        base_icms=Decimal(
            resultado_calculo.base_icms
        ),
        aliquota_icms=_extrair_aliquota(
            resultado_calculo,
            "icms",
        ),
        percentual_reducao_base_icms=(
            _extrair_reducao(resultado_calculo)
        ),
        valor_icms_bruto=Decimal(
            resultado_calculo.valor_icms_bruto
        ),
        percentual_diferimento_icms=(
            _extrair_diferimento(resultado_calculo)
        ),
        valor_icms_diferido=Decimal(
            resultado_calculo.valor_icms_diferido
        ),
        valor_icms=Decimal(
            resultado_calculo.valor_icms
        ),
        base_fcp=Decimal(
            resultado_calculo.base_fcp
        ),
        aliquota_fcp=_extrair_aliquota(
            resultado_calculo,
            "fcp",
        ),
        valor_fcp=Decimal(
            resultado_calculo.valor_fcp
        ),
        base_pis=Decimal(
            resultado_calculo.base_pis
        ),
        aliquota_pis=_extrair_aliquota(
            resultado_calculo,
            "pis",
        ),
        valor_pis=Decimal(
            resultado_calculo.valor_pis
        ),
        base_cofins=Decimal(
            resultado_calculo.base_cofins
        ),
        aliquota_cofins=_extrair_aliquota(
            resultado_calculo,
            "cofins",
        ),
        valor_cofins=Decimal(
            resultado_calculo.valor_cofins
        ),
        base_ipi=Decimal(
            resultado_calculo.base_ipi
        ),
        aliquota_ipi=_extrair_aliquota(
            resultado_calculo,
            "ipi",
        ),
        valor_ipi=Decimal(
            resultado_calculo.valor_ipi
        ),
        valor_total_tributos=Decimal(
            resultado_calculo.valor_total_tributos
        ),
    )


def persistir_item_venda_fiscal(
    *,
    item_venda,
    dados,
):
    if ItemVendaFiscal.objects.filter(
        item_venda=item_venda
    ).exists():
        raise ValidationError(
            "O item ja possui snapshot fiscal."
        )

    payload = asdict(dados)

    return ItemVendaFiscal.objects.create(
        item_venda=item_venda,
        **payload,
    )


def consolidar_dados_venda_fiscal(
    *,
    venda,
    contexto_tributario,
    snapshots_itens,
    configuracao_fiscal_id_original=None,
):
    itens = list(snapshots_itens)

    def somar(campo):
        return sum(
            (
                Decimal(getattr(item, campo))
                for item in itens
            ),
            ZERO,
        )

    return DadosVendaFiscal(
        configuracao_fiscal_id_original=(
            configuracao_fiscal_id_original
        ),
        regime_tributario=str(
            _obter(
                contexto_tributario,
                "regime_tributario",
                "",
            )
        ),
        uf_origem=str(
            _obter(
                contexto_tributario,
                "uf_origem",
                "",
            )
        ),
        uf_destino=str(
            _obter(
                contexto_tributario,
                "uf_destino",
                "",
            )
        ),
        tipo_operacao=str(
            _obter(
                contexto_tributario,
                "tipo_operacao",
                "",
            )
        ),
        finalidade_operacao=str(
            _obter(
                contexto_tributario,
                "finalidade_operacao",
                "",
            )
        ),
        contribuinte_icms=bool(
            _obter(
                contexto_tributario,
                "contribuinte_icms",
                False,
            )
        ),
        consumidor_final=bool(
            _obter(
                contexto_tributario,
                "consumidor_final",
                True,
            )
        ),
        total_base_operacao=somar(
            "base_operacao"
        ),
        total_base_icms=somar("base_icms"),
        total_icms=somar("valor_icms"),
        total_fcp=somar("valor_fcp"),
        total_base_pis=somar("base_pis"),
        total_pis=somar("valor_pis"),
        total_base_cofins=somar(
            "base_cofins"
        ),
        total_cofins=somar("valor_cofins"),
        total_base_ipi=somar("base_ipi"),
        total_ipi=somar("valor_ipi"),
        total_tributos=somar(
            "valor_total_tributos"
        ),
    )


def persistir_venda_fiscal(
    *,
    venda,
    dados,
):
    if VendaFiscal.objects.filter(
        venda=venda
    ).exists():
        raise ValidationError(
            "A venda ja possui snapshot fiscal."
        )

    payload = asdict(dados)

    return VendaFiscal.objects.create(
        venda=venda,
        **payload,
    )