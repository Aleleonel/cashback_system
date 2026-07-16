from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from estoque.choices import TipoMovimentacao

from .entradas import registrar_entrada_estoque
from .saidas import registrar_saida_estoque


def registrar_ajuste_estoque(
    *,
    matriz,
    loja,
    produto,
    origem,
    quantidade_ajuste,
    chave_idempotencia,
    motivo,
    usuario=None,
    documento_referencia='',
    origem_id='',
    request=None,
):
    quantidade_ajuste = _normalizar_quantidade_ajuste(
        quantidade_ajuste
    )

    motivo = _normalizar_motivo(motivo)

    if quantidade_ajuste > Decimal('0.000'):
        return registrar_entrada_estoque(
            matriz=matriz,
            loja=loja,
            produto=produto,
            tipo=TipoMovimentacao.AJUSTE_POSITIVO,
            origem=origem,
            quantidade=quantidade_ajuste,
            chave_idempotencia=chave_idempotencia,
            usuario=usuario,
            observacao=motivo,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            request=request,
        )

    return registrar_saida_estoque(
        matriz=matriz,
        loja=loja,
        produto=produto,
        tipo=TipoMovimentacao.AJUSTE_NEGATIVO,
        origem=origem,
        quantidade=abs(quantidade_ajuste),
        chave_idempotencia=chave_idempotencia,
        usuario=usuario,
        observacao=motivo,
        documento_referencia=documento_referencia,
        origem_id=origem_id,
        request=request,
    )


def _normalizar_quantidade_ajuste(quantidade_ajuste):
    try:
        quantidade_ajuste = Decimal(
            str(quantidade_ajuste)
        )

        if not quantidade_ajuste.is_finite():
            raise InvalidOperation

        quantidade_ajuste = quantidade_ajuste.quantize(
            Decimal('0.001')
        )

    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({
            'quantidade_ajuste': (
                'Informe uma quantidade de ajuste válida.'
            )
        })

    if quantidade_ajuste == Decimal('0.000'):
        raise ValidationError({
            'quantidade_ajuste': (
                'A quantidade de ajuste não pode ser zero.'
            )
        })

    return quantidade_ajuste


def _normalizar_motivo(motivo):
    motivo = (
        motivo or ''
    ).strip()

    if not motivo:
        raise ValidationError({
            'motivo': (
                'O motivo do ajuste é obrigatório.'
            )
        })

    return motivo
