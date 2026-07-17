import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from estoque.choices import (
    OrigemMovimentacao,
    TipoMovimentacao,
)

from .entradas import registrar_entrada_estoque
from .resultados import ResultadoTransferenciaEstoque
from .saidas import registrar_saida_estoque


@transaction.atomic
def registrar_transferencia_estoque(
    *,
    matriz,
    loja_origem,
    loja_destino,
    produto,
    quantidade,
    chave_idempotencia,
    motivo,
    usuario=None,
    documento_referencia='',
    origem_id='',
    request=None,
):
    chave_idempotencia = _normalizar_chave_idempotencia(
        chave_idempotencia
    )

    motivo = _normalizar_motivo(motivo)

    _validar_lojas(
        matriz=matriz,
        loja_origem=loja_origem,
        loja_destino=loja_destino,
    )

    grupo_transferencia = _gerar_grupo_transferencia(
        matriz=matriz,
        chave_idempotencia=chave_idempotencia,
    )

    chave_saida = (
        f'{chave_idempotencia}:saida'
    )

    chave_entrada = (
        f'{chave_idempotencia}:entrada'
    )

    origem_id_saida = _montar_origem_id(
        origem_id=origem_id,
        sufixo='saida',
    )

    origem_id_entrada = _montar_origem_id(
        origem_id=origem_id,
        sufixo='entrada',
    )

    resultado_origem = registrar_saida_estoque(
        matriz=matriz,
        loja=loja_origem,
        produto=produto,
        tipo=TipoMovimentacao.TRANSFERENCIA_SAIDA,
        origem=OrigemMovimentacao.TRANSFERENCIA,
        quantidade=quantidade,
        chave_idempotencia=chave_saida,
        usuario=usuario,
        observacao=motivo,
        documento_referencia=documento_referencia,
        origem_id=origem_id_saida,
        request=request,
        grupo_transferencia=grupo_transferencia,
    )

    resultado_destino = registrar_entrada_estoque(
        matriz=matriz,
        loja=loja_destino,
        produto=produto,
        tipo=TipoMovimentacao.TRANSFERENCIA_ENTRADA,
        origem=OrigemMovimentacao.TRANSFERENCIA,
        quantidade=quantidade,
        chave_idempotencia=chave_entrada,
        usuario=usuario,
        observacao=motivo,
        documento_referencia=documento_referencia,
        origem_id=origem_id_entrada,
        request=request,
        grupo_transferencia=grupo_transferencia,
    )

    _validar_resultados_transferencia(
        grupo_transferencia=grupo_transferencia,
        resultado_origem=resultado_origem,
        resultado_destino=resultado_destino,
    )

    return ResultadoTransferenciaEstoque(
        grupo_transferencia=grupo_transferencia,
        origem=resultado_origem,
        destino=resultado_destino,
    )


def _normalizar_chave_idempotencia(chave_idempotencia):
    chave_idempotencia = (
        chave_idempotencia or ''
    ).strip()

    if not chave_idempotencia:
        raise ValidationError({
            'chave_idempotencia': (
                'A chave de idempotência da transferência '
                'é obrigatória.'
            )
        })

    return chave_idempotencia


def _normalizar_motivo(motivo):
    motivo = (
        motivo or ''
    ).strip()

    if not motivo:
        raise ValidationError({
            'motivo': (
                'O motivo da transferência é obrigatório.'
            )
        })

    return motivo


def _validar_lojas(
    *,
    matriz,
    loja_origem,
    loja_destino,
):
    erros = {}

    if loja_origem.pk == loja_destino.pk:
        erros['loja_destino'] = (
            'A loja de destino deve ser diferente '
            'da loja de origem.'
        )

    if loja_origem.matriz_id != matriz.pk:
        erros['loja_origem'] = (
            'A loja de origem deve pertencer '
            'à matriz informada.'
        )

    if loja_destino.matriz_id != matriz.pk:
        erros['loja_destino'] = (
            'A loja de destino deve pertencer '
            'à matriz informada.'
        )

    if erros:
        raise ValidationError(erros)


def _gerar_grupo_transferencia(
    *,
    matriz,
    chave_idempotencia,
):
    identificador = (
        f'estoque-transferencia:'
        f'{matriz.pk}:'
        f'{chave_idempotencia}'
    )

    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        identificador,
    )


def _montar_origem_id(
    *,
    origem_id,
    sufixo,
):
    origem_id = (
        origem_id or ''
    ).strip()

    if origem_id:
        return f'{origem_id}:{sufixo}'

    return sufixo


def _validar_resultados_transferencia(
    *,
    grupo_transferencia,
    resultado_origem,
    resultado_destino,
):
    movimentacao_origem = resultado_origem.movimentacao
    movimentacao_destino = resultado_destino.movimentacao

    erros = {}

    if (
        movimentacao_origem.grupo_transferencia
        != grupo_transferencia
    ):
        erros['grupo_transferencia'] = (
            'A movimentação de saída possui grupo inválido.'
        )

    if (
        movimentacao_destino.grupo_transferencia
        != grupo_transferencia
    ):
        erros['grupo_transferencia'] = (
            'A movimentação de entrada possui grupo inválido.'
        )

    if (
        movimentacao_origem.produto_id
        != movimentacao_destino.produto_id
    ):
        erros['produto'] = (
            'As movimentações da transferência devem '
            'possuir o mesmo produto.'
        )

    if (
        movimentacao_origem.quantidade
        != movimentacao_destino.quantidade
    ):
        erros['quantidade'] = (
            'As movimentações da transferência devem '
            'possuir a mesma quantidade.'
        )

    duplicidade_consistente = (
        resultado_origem.duplicada
        == resultado_destino.duplicada
    )

    if not duplicidade_consistente:
        erros['chave_idempotencia'] = (
            'A transferência possui reprocessamento parcial.'
        )

    if erros:
        raise ValidationError(erros)
