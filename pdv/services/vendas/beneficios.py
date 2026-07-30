from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from cashback.services.validacoes import (
    validar_limite_beneficios,
    validar_voucher_pre_venda,
)
from vouchers.services import registrar_uso_voucher


CENTAVOS = Decimal("0.01")


@dataclass(frozen=True)
class BeneficioResolvido:
    tipo: str
    valor: Decimal
    voucher: object = None
    codigo: str = ""

    @classmethod
    def nenhum(cls):
        return cls(
            tipo="nenhum",
            valor=Decimal("0.00"),
            voucher=None,
            codigo="",
        )


def _decimal_monetario(valor, *, campo):
    try:
        return Decimal(str(valor or "0").replace(",", ".")).quantize(CENTAVOS)
    except Exception as erro:
        raise ValidationError({
            campo: "Informe um valor monetário válido."
        }) from erro


def resolver_beneficio_da_venda(
    *,
    matriz,
    loja,
    valor_compra,
    tipo_beneficio="nenhum",
    valor_cashback=0,
    codigo_voucher="",
    cliente=None,
):
    """
    Adapta a venda do PDV às regras comerciais compartilhadas.

    Não registra uso, não altera voucher, não consome cashback e não
    persiste dados. Apenas valida e resolve o benefício solicitado.
    """
    tipo = (tipo_beneficio or "nenhum").strip().lower()
    valor_compra = _decimal_monetario(valor_compra, campo="valor_compra")

    if valor_compra <= Decimal("0.00"):
        raise ValidationError({
            "valor_compra": "O valor da compra precisa ser maior que zero."
        })

    if tipo not in {"nenhum", "voucher", "cashback"}:
        raise ValidationError({
            "beneficio": "Escolha um benefício válido."
        })

    if tipo == "nenhum":
        return BeneficioResolvido.nenhum()

    if tipo == "cashback":
        cashback = _decimal_monetario(
            valor_cashback,
            campo="cashback",
        )

        validar_limite_beneficios(
            matriz=matriz,
            valor_compra=valor_compra,
            valor_cashback_usado=cashback,
            valor_desconto_voucher=Decimal("0.00"),
        )

        return BeneficioResolvido(
            tipo="cashback",
            valor=cashback,
            voucher=None,
            codigo="",
        )

    codigo = (codigo_voucher or "").strip().upper()

    if not codigo:
        raise ValidationError({
            "voucher": "Informe o voucher escolhido."
        })

    resultado = validar_voucher_pre_venda(
        matriz=matriz,
        loja=loja,
        cliente=cliente,
        codigo_voucher=codigo,
        valor_compra=valor_compra,
    )
    desconto = Decimal(resultado["desconto"]).quantize(CENTAVOS)

    validar_limite_beneficios(
        matriz=matriz,
        valor_compra=valor_compra,
        valor_cashback_usado=Decimal("0.00"),
        valor_desconto_voucher=desconto,
    )

    return BeneficioResolvido(
        tipo="voucher",
        valor=desconto,
        voucher=resultado["voucher"],
        codigo=resultado["voucher"].codigo,
    )


def registrar_voucher_da_venda(
    *,
    venda,
    usuario,
    beneficio,
    compra,
):
    """
    Registra o uso por meio do único serviço oficial do módulo vouchers.
    """
    if beneficio.tipo != "voucher" or beneficio.voucher is None:
        return None

    if venda.cliente_id is None:
        raise ValidationError({
            "cliente": "Identifique o cliente para utilizar o voucher."
        })

    return registrar_uso_voucher(
        matriz=venda.matriz,
        loja=venda.loja,
        cliente=venda.cliente,
        voucher=beneficio.voucher,
        usuario=usuario,
        compra=compra,
        valor_compra=venda.subtotal,
        valor_desconto=beneficio.valor,
        observacao=f"Voucher utilizado na venda PDV #{venda.pk}.",
    )
