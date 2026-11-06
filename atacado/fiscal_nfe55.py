from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import ModeloFiscalPedidoAtacado, TipoEmissaoPedidoAtacado

UFS_BRASIL = frozenset({
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
})


@dataclass(frozen=True)
class DadosNFe55Atacado:
    pedido_id: int | None
    matriz_id: int | None
    loja_id: int
    cliente_id: int | None
    modelo: str
    uf_destino: str
    subtotal_produtos: Decimal
    desconto_atacado: Decimal
    ajustes_negociados: Decimal
    frete: Decimal
    total: Decimal


def preparar_dados_nfe55_atacado(pedido):
    """Prepara o contrato comercial para futura NF-e 55, sem emitir/transmitir."""
    if pedido.tipo_emissao != TipoEmissaoPedidoAtacado.FISCAL:
        raise ValidationError("O pedido precisa estar marcado para emissao fiscal.")

    if pedido.modelo_fiscal != ModeloFiscalPedidoAtacado.NFE:
        raise ValidationError("O Atacado fiscal utiliza NF-e modelo 55.")

    if not pedido.loja_id:
        raise ValidationError("A loja emissora e obrigatoria para NF-e 55.")

    uf = (pedido.uf_destino_fiscal or "").strip().upper()
    if uf not in UFS_BRASIL:
        raise ValidationError("UF de destino fiscal invalida.")

    return DadosNFe55Atacado(
        pedido_id=getattr(pedido, "pk", None),
        matriz_id=getattr(pedido, "matriz_id", None),
        loja_id=pedido.loja_id,
        cliente_id=getattr(pedido, "cliente_id", None),
        modelo=str(ModeloFiscalPedidoAtacado.NFE),
        uf_destino=uf,
        subtotal_produtos=pedido.subtotal_produtos,
        desconto_atacado=pedido.desconto_atacado,
        ajustes_negociados=pedido.ajustes_negociados,
        frete=pedido.frete,
        total=pedido.total,
    )
