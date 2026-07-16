from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from estoque.choices import (
    NaturezaMovimentacao,
    get_natureza_tipo_movimentacao,
)
from estoque.models import MovimentacaoEstoque, SaldoEstoque
from produtos.models import Produto

from .resultados import ResultadoMovimentacaoEstoque


def registrar_entrada_estoque(
    *,
    matriz,
    loja,
    produto,
    tipo,
    origem,
    quantidade,
    chave_idempotencia,
    usuario=None,
    observacao='',
    documento_referencia='',
    origem_id='',
    request=None,
    grupo_transferencia=None,
    movimentacao_origem=None,
):
    chave_idempotencia = _normalizar_chave_idempotencia(
        chave_idempotencia
    )

    quantidade = _normalizar_quantidade(quantidade)

    observacao = _normalizar_texto(observacao)
    documento_referencia = _normalizar_texto(
        documento_referencia
    )
    origem_id = _normalizar_texto(origem_id)

    _validar_contexto(
        matriz=matriz,
        loja=loja,
        produto=produto,
    )

    _validar_tipo_entrada(tipo=tipo)

    resultado_idempotente = _resolver_idempotencia(
        matriz=matriz,
        loja=loja,
        produto=produto,
        tipo=tipo,
        origem=origem,
        quantidade=quantidade,
        chave_idempotencia=chave_idempotencia,
        documento_referencia=documento_referencia,
        origem_id=origem_id,
        grupo_transferencia=grupo_transferencia,
        movimentacao_origem=movimentacao_origem,
    )

    if resultado_idempotente is not None:
        return resultado_idempotente

    try:
        return _registrar_entrada_estoque_atomic(
            matriz=matriz,
            loja=loja,
            produto=produto,
            tipo=tipo,
            origem=origem,
            quantidade=quantidade,
            chave_idempotencia=chave_idempotencia,
            usuario=usuario,
            observacao=observacao,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            request=request,
            grupo_transferencia=grupo_transferencia,
            movimentacao_origem=movimentacao_origem,
        )

    except IntegrityError:
        resultado_idempotente = _resolver_idempotencia(
            matriz=matriz,
            loja=loja,
            produto=produto,
            tipo=tipo,
            origem=origem,
            quantidade=quantidade,
            chave_idempotencia=chave_idempotencia,
            documento_referencia=documento_referencia,
            origem_id=origem_id,
            grupo_transferencia=grupo_transferencia,
            movimentacao_origem=movimentacao_origem,
        )

        if resultado_idempotente is None:
            raise

        return resultado_idempotente


@transaction.atomic
def _registrar_entrada_estoque_atomic(
    *,
    matriz,
    loja,
    produto,
    tipo,
    origem,
    quantidade,
    chave_idempotencia,
    usuario=None,
    observacao='',
    documento_referencia='',
    origem_id='',
    request=None,
    grupo_transferencia=None,
    movimentacao_origem=None,
):
    saldo, saldo_criado = _obter_saldo_bloqueado(
        matriz=matriz,
        loja=loja,
        produto=produto,
    )

    saldo_anterior = saldo.quantidade_atual
    saldo_posterior = saldo_anterior + quantidade
    momento_movimentacao = timezone.now()

    movimentacao = MovimentacaoEstoque.objects.create(
        matriz=matriz,
        loja=loja,
        produto=produto,
        tipo=tipo,
        natureza=NaturezaMovimentacao.ENTRADA,
        quantidade=quantidade,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        usuario=usuario,
        observacao=observacao,
        documento_referencia=documento_referencia,
        origem=origem,
        origem_id=origem_id,
        chave_idempotencia=chave_idempotencia,
        grupo_transferencia=grupo_transferencia,
        movimentacao_origem=movimentacao_origem,
    )

    _atualizar_saldo(
        saldo=saldo,
        saldo_posterior=saldo_posterior,
        momento_movimentacao=momento_movimentacao,
    )

    _registrar_auditoria_movimentacao(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        produto=produto,
        tipo=tipo,
        quantidade=quantidade,
        saldo_anterior=saldo_anterior,
        saldo_posterior=saldo_posterior,
        saldo_criado=saldo_criado,
        movimentacao=movimentacao,
        request=request,
    )

    return ResultadoMovimentacaoEstoque(
        saldo=saldo,
        movimentacao=movimentacao,
        duplicada=False,
    )


def _normalizar_chave_idempotencia(chave_idempotencia):
    chave_idempotencia = _normalizar_texto(
        chave_idempotencia
    )

    if not chave_idempotencia:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotência é obrigatória.'
            )
        })

    return chave_idempotencia


def _normalizar_texto(valor):
    return (
        valor or ''
    ).strip()


def _normalizar_quantidade(quantidade):
    try:
        quantidade = Decimal(str(quantidade))

        if not quantidade.is_finite():
            raise InvalidOperation

        quantidade = quantidade.quantize(
            Decimal('0.001')
        )

    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({
            'quantidade': (
                'Informe uma quantidade válida.'
            )
        })

    if quantidade <= Decimal('0.000'):
        raise ValidationError({
            'quantidade': (
                'A quantidade deve ser maior que zero.'
            )
        })

    return quantidade


def _validar_contexto(
    *,
    matriz,
    loja,
    produto,
):
    erros = {}

    if loja.matriz_id != matriz.id:
        erros['loja'] = (
            'A loja deve pertencer à matriz informada.'
        )

    if produto.matriz_id != matriz.id:
        erros['produto'] = (
            'O produto deve pertencer à matriz informada.'
        )

    if not produto.controla_estoque:
        erros['produto'] = (
            'O produto informado não controla estoque.'
        )

    if erros:
        raise ValidationError(erros)


def _validar_tipo_entrada(*, tipo):
    natureza = get_natureza_tipo_movimentacao(tipo)

    if natureza != NaturezaMovimentacao.ENTRADA:
        raise ValidationError({
            'tipo': (
                'O tipo informado não representa uma entrada de estoque.'
            )
        })


def _resolver_idempotencia(
    *,
    matriz,
    loja,
    produto,
    tipo,
    origem,
    quantidade,
    chave_idempotencia,
    documento_referencia,
    origem_id,
    grupo_transferencia,
    movimentacao_origem,
):
    movimentacao = _buscar_movimentacao_idempotente(
        matriz=matriz,
        chave_idempotencia=chave_idempotencia,
    )

    if movimentacao is None:
        return None

    _validar_reprocessamento_idempotente(
        movimentacao=movimentacao,
        loja=loja,
        produto=produto,
        tipo=tipo,
        origem=origem,
        quantidade=quantidade,
        documento_referencia=documento_referencia,
        origem_id=origem_id,
        grupo_transferencia=grupo_transferencia,
        movimentacao_origem=movimentacao_origem,
    )

    return _criar_resultado_duplicado(
        movimentacao=movimentacao
    )


def _buscar_movimentacao_idempotente(
    *,
    matriz,
    chave_idempotencia,
):
    return (
        MovimentacaoEstoque.objects
        .filter(
            matriz=matriz,
            chave_idempotencia=chave_idempotencia,
        )
        .select_related(
            'matriz',
            'loja',
            'produto',
            'movimentacao_origem',
        )
        .first()
    )


def _validar_reprocessamento_idempotente(
    *,
    movimentacao,
    loja,
    produto,
    tipo,
    origem,
    quantidade,
    documento_referencia,
    origem_id,
    grupo_transferencia,
    movimentacao_origem,
):
    movimentacao_origem_id = (
        movimentacao_origem.pk
        if movimentacao_origem is not None
        else None
    )

    campos_compativeis = (
        movimentacao.loja_id == loja.pk
        and movimentacao.produto_id == produto.pk
        and movimentacao.tipo == tipo
        and movimentacao.origem == origem
        and movimentacao.quantidade == quantidade
        and (
            movimentacao.documento_referencia
            == documento_referencia
        )
        and movimentacao.origem_id == origem_id
        and (
            movimentacao.grupo_transferencia
            == grupo_transferencia
        )
        and (
            movimentacao.movimentacao_origem_id
            == movimentacao_origem_id
        )
    )

    if not campos_compativeis:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotência já foi utilizada '
                'por uma operação diferente.'
            )
        })


def _obter_saldo_bloqueado(
    *,
    matriz,
    loja,
    produto,
):
    Produto.objects.select_for_update().get(
        pk=produto.pk
    )

    saldo, saldo_criado = SaldoEstoque.objects.get_or_create(
        matriz=matriz,
        loja=loja,
        produto=produto,
        defaults={
            'quantidade_atual': Decimal('0.000'),
        }
    )

    saldo = (
        SaldoEstoque.objects
        .select_for_update()
        .get(pk=saldo.pk)
    )

    return saldo, saldo_criado


def _atualizar_saldo(
    *,
    saldo,
    saldo_posterior,
    momento_movimentacao,
):
    saldo.quantidade_atual = saldo_posterior
    saldo.ultima_movimentacao_em = momento_movimentacao

    saldo.save(
        update_fields=[
            'quantidade_atual',
            'ultima_movimentacao_em',
            'atualizado_em',
        ]
    )


def _registrar_auditoria_movimentacao(
    *,
    usuario,
    matriz,
    loja,
    produto,
    tipo,
    quantidade,
    saldo_anterior,
    saldo_posterior,
    saldo_criado,
    movimentacao,
    request,
):
    registrar_auditoria(
        usuario=usuario,
        matriz=matriz,
        loja=loja,
        acao=RegistroAuditoria.ACAO_CRIAR,
        recurso='estoque.movimentacao',
        recurso_id=movimentacao.uuid,
        descricao=(
            f'Entrada de estoque: '
            f'produto={produto.codigo_interno}; '
            f'tipo={tipo}; '
            f'quantidade={quantidade}; '
            f'saldo_anterior={saldo_anterior}; '
            f'saldo_posterior={saldo_posterior}; '
            f'saldo_criado={saldo_criado}.'
        ),
        request=request,
    )


def _criar_resultado_duplicado(*, movimentacao):
    saldo = SaldoEstoque.objects.get(
        matriz=movimentacao.matriz,
        loja=movimentacao.loja,
        produto=movimentacao.produto,
    )

    return ResultadoMovimentacaoEstoque(
        saldo=saldo,
        movimentacao=movimentacao,
        duplicada=True,
    )
