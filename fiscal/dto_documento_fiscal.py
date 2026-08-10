from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DadosItemDocumentoFiscal:
    item_venda_id: int

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
class DadosDocumentoFiscal:
    venda_fiscal_id: int
    venda_id: int
    matriz_id: int
    loja_id: int

    modelo: str
    ambiente: str
    serie: int
    numero: int | None

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

    itens: tuple[DadosItemDocumentoFiscal, ...]