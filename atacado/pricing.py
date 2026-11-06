from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from configuracoes.models import ConfiguracaoComercial
from configuracoes.services_atacado import obter_faixa_atacado


CENTAVOS = Decimal("0.01")


def dinheiro(valor):
    return Decimal(str(valor or 0)).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class ItemPrecificacao:
    produto: object
    quantidade: Decimal
    preco_unitario: Decimal

    @property
    def subtotal(self):
        return dinheiro(Decimal(str(self.quantidade)) * Decimal(str(self.preco_unitario)))


@dataclass(frozen=True)
class ResultadoItemAtacado:
    produto: object
    quantidade: Decimal
    preco_unitario_original: Decimal
    preco_unitario_base: Decimal
    preco_unitario_final: Decimal
    subtotal_base: Decimal
    desconto_atacado: Decimal
    produto_promocional: bool
    atacado_elegivel: bool
    conta_para_enquadramento: bool


@dataclass(frozen=True)
class ResultadoPrecificacaoAtacado:
    base_enquadramento: Decimal
    faixa: object
    percentual_desconto: Decimal
    subtotal_produtos: Decimal
    desconto_atacado: Decimal
    total_produtos: Decimal
    itens: tuple


def _configuracao(matriz):
    return ConfiguracaoComercial.objects.get(matriz=matriz)


def precificar_atacado(*, matriz, itens):
    config = _configuracao(matriz)
    # F32M4S4_POLITICA_UNIFICADA: parametros comerciais da Matriz.
    if not config.atacado_ativo:
        raise ValidationError("O atacado esta desativado para esta Matriz.")
    normalizados = []
    base_enquadramento = Decimal("0.00")
    subtotal_produtos = Decimal("0.00")

    for entrada in itens:
        produto = entrada.produto
        quantidade = Decimal(str(entrada.quantidade))
        preco = dinheiro(entrada.preco_unitario)
        subtotal = dinheiro(quantidade * preco)
        promocional = bool(getattr(produto, "promocional", False))
        elegivel = bool(getattr(produto, "atacado_elegivel", True))
        conta = (not promocional) or bool(config.produto_promocional_conta_para_faixa_atacado)

        if conta:
            base_enquadramento += subtotal
        subtotal_produtos += subtotal
        normalizados.append((produto, quantidade, preco, subtotal, promocional, elegivel, conta))

    base_enquadramento = dinheiro(base_enquadramento)
    subtotal_produtos = dinheiro(subtotal_produtos)
    minimo = dinheiro(config.pedido_minimo_atacado)
    if minimo > 0 and subtotal_produtos < minimo:
        raise ValidationError(f"O pedido minimo do atacado e R$ {minimo:.2f}.")
    faixa = obter_faixa_atacado(config, base_enquadramento)
    percentual = Decimal(str(faixa.percentual_desconto)) if faixa else Decimal("0")
    fator = percentual / Decimal("100")

    resultados = []
    desconto_total = Decimal("0.00")
    for produto, quantidade, preco, subtotal, promocional, elegivel, conta in normalizados:
        # Produto promocional nunca recebe desconto atacadista automático.
        recebe_desconto = bool(faixa) and elegivel and not promocional
        desconto = dinheiro(subtotal * fator) if recebe_desconto else Decimal("0.00")
        total_item = dinheiro(subtotal - desconto)
        preco_final = dinheiro(total_item / quantidade) if quantidade else preco
        desconto_total += desconto
        resultados.append(ResultadoItemAtacado(
            produto=produto,
            quantidade=quantidade,
            preco_unitario_original=preco,
            preco_unitario_base=preco,
            preco_unitario_final=preco_final,
            subtotal_base=subtotal,
            desconto_atacado=desconto,
            produto_promocional=promocional,
            atacado_elegivel=elegivel,
            conta_para_enquadramento=conta,
        ))

    desconto_total = dinheiro(desconto_total)
    return ResultadoPrecificacaoAtacado(
        base_enquadramento=base_enquadramento,
        faixa=faixa,
        percentual_desconto=percentual,
        subtotal_produtos=subtotal_produtos,
        desconto_atacado=desconto_total,
        total_produtos=dinheiro(subtotal_produtos - desconto_total),
        itens=tuple(resultados),
    )
