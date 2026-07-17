"""Servicos para reversao de movimentacoes de estoque."""

from django.core.exceptions import ValidationError
from django.db import transaction

from estoque.choices import (
    NaturezaMovimentacao,
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.models import MovimentacaoEstoque, SaldoEstoque

from .entradas import registrar_entrada_estoque
from .resultados import ResultadoMovimentacaoEstoque
from .saidas import registrar_saida_estoque


TIPOS_REVERSAO = {
    TipoMovimentacao.REVERSAO_ENTRADA,
    TipoMovimentacao.REVERSAO_SAIDA,
}


@transaction.atomic
def registrar_reversao_estoque(
    *,
    movimentacao_origem,
    chave_idempotencia,
    motivo,
    usuario=None,
    documento_referencia='',
    origem_id='',
    request=None,
):
    """
    Reverte integralmente uma movimentacao de estoque.

    Uma movimentacao de entrada e revertida por uma saida.
    Uma movimentacao de saida e revertida por uma entrada.

    A reversao sempre utiliza:

    - a mesma matriz;
    - a mesma loja;
    - o mesmo produto;
    - a mesma quantidade da movimentacao original.

    A operacao e atomica e idempotente.
    """

    chave_idempotencia = _normalizar_chave_idempotencia(
        chave_idempotencia
    )

    motivo = _normalizar_motivo(motivo)

    documento_referencia = _normalizar_texto(
        documento_referencia
    )

    origem_id = _normalizar_texto(origem_id)

    movimentacao_origem = _obter_movimentacao_bloqueada(
        movimentacao_origem=movimentacao_origem
    )

    _validar_movimentacao_original(
        movimentacao_origem=movimentacao_origem
    )

    if not origem_id:
        origem_id = str(movimentacao_origem.uuid)

    reversao_existente = _buscar_reversao_existente(
        movimentacao_origem=movimentacao_origem
    )

    if reversao_existente is not None:
        return _resolver_reversao_existente(
            reversao=reversao_existente,
            chave_idempotencia=chave_idempotencia,
            motivo=motivo,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
        )

    if (
        movimentacao_origem.natureza
        == NaturezaMovimentacao.ENTRADA
    ):
        return registrar_saida_estoque(
            matriz=movimentacao_origem.matriz,
            loja=movimentacao_origem.loja,
            produto=movimentacao_origem.produto,
            tipo=TipoMovimentacao.REVERSAO_SAIDA,
            origem=OrigemMovimentacao.SISTEMA,
            quantidade=movimentacao_origem.quantidade,
            chave_idempotencia=chave_idempotencia,
            usuario=usuario,
            observacao=motivo,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            request=request,
            movimentacao_origem=movimentacao_origem,
        )

    if (
        movimentacao_origem.natureza
        == NaturezaMovimentacao.SAIDA
    ):
        return registrar_entrada_estoque(
            matriz=movimentacao_origem.matriz,
            loja=movimentacao_origem.loja,
            produto=movimentacao_origem.produto,
            tipo=TipoMovimentacao.REVERSAO_ENTRADA,
            origem=OrigemMovimentacao.SISTEMA,
            quantidade=movimentacao_origem.quantidade,
            chave_idempotencia=chave_idempotencia,
            usuario=usuario,
            observacao=motivo,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            request=request,
            movimentacao_origem=movimentacao_origem,
        )

    raise ValidationError({
        'movimentacao_origem': (
            'A natureza da movimentacao original e invalida.'
        )
    })


def _normalizar_chave_idempotencia(chave_idempotencia):
    chave_idempotencia = _normalizar_texto(
        chave_idempotencia
    )

    if not chave_idempotencia:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotencia da reversao e obrigatoria.'
            )
        })

    return chave_idempotencia


def _normalizar_motivo(motivo):
    motivo = _normalizar_texto(motivo)

    if not motivo:
        raise ValidationError({
            'motivo': (
                'O motivo da reversao e obrigatorio.'
            )
        })

    return motivo


def _normalizar_texto(valor):
    return (
        valor or ''
    ).strip()


def _obter_movimentacao_bloqueada(
    *,
    movimentacao_origem,
):
    if (
        movimentacao_origem is None
        or not getattr(movimentacao_origem, 'pk', None)
    ):
        raise ValidationError({
            'movimentacao_origem': (
                'Informe uma movimentacao original valida.'
            )
        })

    try:
        return (
            MovimentacaoEstoque.objects
            .select_for_update()
            .select_related(
                'matriz',
                'loja',
                'produto',
                'movimentacao_origem',
            )
            .get(pk=movimentacao_origem.pk)
        )

    except MovimentacaoEstoque.DoesNotExist:
        raise ValidationError({
            'movimentacao_origem': (
                'A movimentacao original nao foi encontrada.'
            )
        })


def _validar_movimentacao_original(
    *,
    movimentacao_origem,
):
    if movimentacao_origem.tipo in TIPOS_REVERSAO:
        raise ValidationError({
            'movimentacao_origem': (
                'Nao e permitido reverter outra reversao.'
            )
        })


def _buscar_reversao_existente(
    *,
    movimentacao_origem,
):
    return (
        MovimentacaoEstoque.objects
        .filter(
            movimentacao_origem=movimentacao_origem
        )
        .select_related(
            'matriz',
            'loja',
            'produto',
            'movimentacao_origem',
        )
        .first()
    )


def _resolver_reversao_existente(
    *,
    reversao,
    chave_idempotencia,
    motivo,
    documento_referencia,
    origem_id,
):
    if reversao.chave_idempotencia != chave_idempotencia:
        raise ValidationError({
            'movimentacao_origem': (
                'A movimentacao informada ja foi revertida.'
            )
        })

    campos_compativeis = (
        reversao.observacao == motivo
        and (
            reversao.documento_referencia
            == documento_referencia
        )
        and reversao.origem_id == origem_id
    )

    if not campos_compativeis:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotencia ja foi utilizada '
                'por uma reversao diferente.'
            )
        })

    saldo = SaldoEstoque.objects.get(
        matriz=reversao.matriz,
        loja=reversao.loja,
        produto=reversao.produto,
    )

    return ResultadoMovimentacaoEstoque(
        saldo=saldo,
        movimentacao=reversao,
        duplicada=True,
    )
