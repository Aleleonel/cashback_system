from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria

from compras.choices import (
    StatusFornecedor,
    StatusPedidoCompra,
)
from compras.models import (
    ItemPedidoCompra,
    PedidoCompra,
)


@transaction.atomic
def criar_pedido_compra(
    *,
    matriz,
    fornecedor,
    data_emissao,
    usuario,
    previsao_entrega=None,
    condicao_pagamento='',
    frete=Decimal('0.00'),
    desconto=Decimal('0.00'),
    observacoes='',
    request=None,
):
    _validar_fornecedor(
        matriz=matriz,
        fornecedor=fornecedor,
    )

    _validar_datas(
        data_emissao=data_emissao,
        previsao_entrega=previsao_entrega,
    )

    frete = _decimal_nao_negativo(
        frete,
        campo='frete',
    )

    desconto = _decimal_nao_negativo(
        desconto,
        campo='desconto',
    )

    MatrizModel = matriz.__class__

    MatrizModel.objects.select_for_update().get(
        pk=matriz.pk
    )

    ultimo_numero = (
        PedidoCompra.objects
        .filter(matriz=matriz)
        .aggregate(maior=Max('numero'))
        .get('maior')
        or 0
    )

    pedido = PedidoCompra.objects.create(
        matriz=matriz,
        fornecedor=fornecedor,
        numero=ultimo_numero + 1,
        status=StatusPedidoCompra.RASCUNHO,
        data_emissao=data_emissao,
        previsao_entrega=previsao_entrega,
        condicao_pagamento=(
            condicao_pagamento or ''
        ).strip(),
        frete=frete,
        desconto=desconto,
        observacoes=(observacoes or '').strip(),
        criado_por=usuario,
    )

    _auditar(
        pedido=pedido,
        usuario=usuario,
        acao=RegistroAuditoria.ACAO_CRIAR,
        descricao=(
            f'Pedido de compra criado: '
            f'numero={pedido.numero}; '
            f'fornecedor={fornecedor.razao_social}.'
        ),
        request=request,
    )

    return pedido


@transaction.atomic
def editar_pedido_compra(
    *,
    pedido,
    fornecedor,
    data_emissao,
    previsao_entrega=None,
    condicao_pagamento='',
    frete=Decimal('0.00'),
    desconto=Decimal('0.00'),
    observacoes='',
    usuario=None,
    request=None,
):
    pedido = _bloquear_pedido(pedido)

    _garantir_rascunho(pedido)

    _validar_fornecedor(
        matriz=pedido.matriz,
        fornecedor=fornecedor,
    )

    _validar_datas(
        data_emissao=data_emissao,
        previsao_entrega=previsao_entrega,
    )

    pedido.fornecedor = fornecedor
    pedido.data_emissao = data_emissao
    pedido.previsao_entrega = previsao_entrega
    pedido.condicao_pagamento = (
        condicao_pagamento or ''
    ).strip()
    pedido.frete = _decimal_nao_negativo(
        frete,
        campo='frete',
    )
    pedido.desconto = _decimal_nao_negativo(
        desconto,
        campo='desconto',
    )
    pedido.observacoes = (
        observacoes or ''
    ).strip()

    pedido.save(
        update_fields=[
            'fornecedor',
            'data_emissao',
            'previsao_entrega',
            'condicao_pagamento',
            'frete',
            'desconto',
            'observacoes',
            'atualizado_em',
        ]
    )

    _auditar(
        pedido=pedido,
        usuario=usuario,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=(
            f'Pedido de compra editado: '
            f'numero={pedido.numero}.'
        ),
        request=request,
    )

    return pedido


@transaction.atomic
def adicionar_item_pedido_compra(
    *,
    pedido,
    produto,
    quantidade,
    valor_unitario,
    observacoes='',
    usuario=None,
    request=None,
):
    pedido = _bloquear_pedido(pedido)

    _garantir_rascunho(pedido)
    _validar_produto(
        matriz=pedido.matriz,
        produto=produto,
    )

    quantidade = _decimal_positivo(
        quantidade,
        campo='quantidade',
    )

    valor_unitario = _decimal_nao_negativo(
        valor_unitario,
        campo='valor_unitario',
    )

    if ItemPedidoCompra.objects.filter(
        pedido=pedido,
        produto=produto,
    ).exists():
        raise ValidationError({
            'produto': (
                'Este produto ja foi adicionado '
                'ao pedido.'
            )
        })

    item = ItemPedidoCompra.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade=quantidade,
        valor_unitario=valor_unitario,
        observacoes=(observacoes or '').strip(),
    )

    _auditar(
        pedido=pedido,
        usuario=usuario,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=(
            f'Item adicionado ao pedido de compra: '
            f'numero={pedido.numero}; '
            f'produto={produto}; '
            f'quantidade={quantidade}.'
        ),
        request=request,
    )

    return item


@transaction.atomic
def remover_item_pedido_compra(
    *,
    item,
    usuario=None,
    request=None,
):
    pedido = _bloquear_pedido(item.pedido)

    _garantir_rascunho(pedido)

    item = (
        ItemPedidoCompra.objects
        .select_for_update()
        .select_related('produto')
        .get(
            pk=item.pk,
            pedido=pedido,
        )
    )

    produto_descricao = str(item.produto)
    item.delete()

    _auditar(
        pedido=pedido,
        usuario=usuario,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=(
            f'Item removido do pedido de compra: '
            f'numero={pedido.numero}; '
            f'produto={produto_descricao}.'
        ),
        request=request,
    )


@transaction.atomic
def enviar_pedido_compra(
    *,
    pedido,
    usuario=None,
    request=None,
):
    pedido = _bloquear_pedido(pedido)

    _garantir_rascunho(pedido)

    if not pedido.itens.exists():
        raise ValidationError(
            'Adicione ao menos um item antes de enviar.'
        )

    pedido.status = StatusPedidoCompra.ENVIADO
    pedido.enviado_em = timezone.now()

    pedido.save(
        update_fields=[
            'status',
            'enviado_em',
            'atualizado_em',
        ]
    )

    _auditar(
        pedido=pedido,
        usuario=usuario,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=(
            f'Pedido de compra enviado: '
            f'numero={pedido.numero}; '
            f'total={pedido.total}.'
        ),
        request=request,
    )

    return pedido


@transaction.atomic
def cancelar_pedido_compra(
    *,
    pedido,
    usuario=None,
    request=None,
):
    pedido = _bloquear_pedido(pedido)

    if pedido.status in {
        StatusPedidoCompra.RECEBIDO,
        StatusPedidoCompra.CANCELADO,
    }:
        raise ValidationError(
            'Este pedido nao pode ser cancelado.'
        )

    pedido.status = StatusPedidoCompra.CANCELADO
    pedido.cancelado_em = timezone.now()

    pedido.save(
        update_fields=[
            'status',
            'cancelado_em',
            'atualizado_em',
        ]
    )

    _auditar(
        pedido=pedido,
        usuario=usuario,
        acao=RegistroAuditoria.ACAO_EDITAR,
        descricao=(
            f'Pedido de compra cancelado: '
            f'numero={pedido.numero}.'
        ),
        request=request,
    )

    return pedido


def _bloquear_pedido(pedido):
    return (
        PedidoCompra.objects
        .select_for_update()
        .select_related(
            'matriz',
            'fornecedor',
        )
        .prefetch_related('itens')
        .get(pk=pedido.pk)
    )


def _garantir_rascunho(pedido):
    if pedido.status != StatusPedidoCompra.RASCUNHO:
        raise ValidationError(
            'Somente pedidos em rascunho podem ser alterados.'
        )


def _validar_fornecedor(
    *,
    matriz,
    fornecedor,
):
    if fornecedor.matriz_id != matriz.pk:
        raise ValidationError({
            'fornecedor': (
                'O fornecedor nao pertence a esta matriz.'
            )
        })

    if fornecedor.status != StatusFornecedor.ATIVO:
        raise ValidationError({
            'fornecedor': (
                'O fornecedor precisa estar ativo.'
            )
        })


def _validar_produto(
    *,
    matriz,
    produto,
):
    nomes_campos = {
        campo.name
        for campo in produto._meta.fields
    }

    if (
        'matriz' in nomes_campos
        and produto.matriz_id != matriz.pk
    ):
        raise ValidationError({
            'produto': (
                'O produto nao pertence a esta matriz.'
            )
        })

    if (
        'ativo' in nomes_campos
        and not produto.ativo
    ):
        raise ValidationError({
            'produto': 'O produto esta inativo.'
        })


def _validar_datas(
    *,
    data_emissao,
    previsao_entrega,
):
    if (
        previsao_entrega
        and previsao_entrega < data_emissao
    ):
        raise ValidationError({
            'previsao_entrega': (
                'A previsao de entrega nao pode ser '
                'anterior a data de emissao.'
            )
        })


def _decimal_positivo(
    valor,
    *,
    campo,
):
    try:
        valor = Decimal(str(valor))
    except Exception as erro:
        raise ValidationError({
            campo: 'Informe um valor numerico valido.'
        }) from erro

    if valor <= 0:
        raise ValidationError({
            campo: 'O valor deve ser maior que zero.'
        })

    return valor


def _decimal_nao_negativo(
    valor,
    *,
    campo,
):
    try:
        valor = Decimal(str(valor or 0))
    except Exception as erro:
        raise ValidationError({
            campo: 'Informe um valor numerico valido.'
        }) from erro

    if valor < 0:
        raise ValidationError({
            campo: 'O valor nao pode ser negativo.'
        })

    return valor


def _auditar(
    *,
    pedido,
    usuario,
    acao,
    descricao,
    request,
):
    registrar_auditoria(
        usuario=usuario,
        matriz=pedido.matriz,
        loja=None,
        acao=acao,
        recurso='compras.pedido_compra',
        recurso_id=pedido.uuid,
        descricao=descricao,
        request=request,
    )