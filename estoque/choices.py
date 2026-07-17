from django.db import models


class NaturezaMovimentacao(models.TextChoices):
    ENTRADA = 'entrada', 'Entrada'
    SAIDA = 'saida', 'Saída'


class TipoMovimentacao(models.TextChoices):
    SALDO_INICIAL = 'saldo_inicial', 'Saldo inicial'

    ENTRADA_MANUAL = 'entrada_manual', 'Entrada manual'
    SAIDA_MANUAL = 'saida_manual', 'Saída manual'

    AJUSTE_POSITIVO = 'ajuste_positivo', 'Ajuste positivo'
    AJUSTE_NEGATIVO = 'ajuste_negativo', 'Ajuste negativo'

    TRANSFERENCIA_ENTRADA = (
        'transferencia_entrada',
        'Transferência - entrada'
    )
    TRANSFERENCIA_SAIDA = (
        'transferencia_saida',
        'Transferência - saída'
    )

    INVENTARIO_ENTRADA = (
        'inventario_entrada',
        'Inventário - entrada'
    )
    INVENTARIO_SAIDA = (
        'inventario_saida',
        'Inventário - saída'
    )

    REVERSAO_ENTRADA = (
        'reversao_entrada',
        'Reversão - entrada'
    )
    REVERSAO_SAIDA = (
        'reversao_saida',
        'Reversão - saída'
    )

    COMPRA = 'compra', 'Compra'
    DEVOLUCAO_COMPRA = 'devolucao_compra', 'Devolução de compra'

    VENDA = 'venda', 'Venda'
    DEVOLUCAO_VENDA = 'devolucao_venda', 'Devolução de venda'


class OrigemMovimentacao(models.TextChoices):
    MANUAL = 'manual', 'Manual'
    INVENTARIO = 'inventario', 'Inventário'
    TRANSFERENCIA = 'transferencia', 'Transferência'
    COMPRA = 'compra', 'Compra'
    VENDA = 'venda', 'Venda'
    FISCAL = 'fiscal', 'Fiscal'
    SISTEMA = 'sistema', 'Sistema'


NATUREZA_POR_TIPO_MOVIMENTACAO = {
    TipoMovimentacao.SALDO_INICIAL: NaturezaMovimentacao.ENTRADA,

    TipoMovimentacao.ENTRADA_MANUAL: NaturezaMovimentacao.ENTRADA,
    TipoMovimentacao.SAIDA_MANUAL: NaturezaMovimentacao.SAIDA,

    TipoMovimentacao.AJUSTE_POSITIVO: NaturezaMovimentacao.ENTRADA,
    TipoMovimentacao.AJUSTE_NEGATIVO: NaturezaMovimentacao.SAIDA,

    TipoMovimentacao.TRANSFERENCIA_ENTRADA: NaturezaMovimentacao.ENTRADA,
    TipoMovimentacao.TRANSFERENCIA_SAIDA: NaturezaMovimentacao.SAIDA,

    TipoMovimentacao.INVENTARIO_ENTRADA: NaturezaMovimentacao.ENTRADA,
    TipoMovimentacao.INVENTARIO_SAIDA: NaturezaMovimentacao.SAIDA,

    TipoMovimentacao.REVERSAO_ENTRADA: NaturezaMovimentacao.ENTRADA,
    TipoMovimentacao.REVERSAO_SAIDA: NaturezaMovimentacao.SAIDA,

    TipoMovimentacao.COMPRA: NaturezaMovimentacao.ENTRADA,
    TipoMovimentacao.DEVOLUCAO_COMPRA: NaturezaMovimentacao.SAIDA,

    TipoMovimentacao.VENDA: NaturezaMovimentacao.SAIDA,
    TipoMovimentacao.DEVOLUCAO_VENDA: NaturezaMovimentacao.ENTRADA,
}


def get_natureza_tipo_movimentacao(tipo):
    return NATUREZA_POR_TIPO_MOVIMENTACAO.get(tipo)


def tipo_movimentacao_compativel_com_natureza(
    *,
    tipo,
    natureza,
):
    natureza_esperada = get_natureza_tipo_movimentacao(tipo)

    return (
        natureza_esperada is not None
        and natureza_esperada == natureza
    )
class StatusReservaEstoque(models.TextChoices):
    ATIVA = 'ativa', 'Ativa'
    CONFIRMADA = 'confirmada', 'Confirmada'
    LIBERADA = 'liberada', 'Liberada'
    CANCELADA = 'cancelada', 'Cancelada'
    EXPIRADA = 'expirada', 'Expirada'
