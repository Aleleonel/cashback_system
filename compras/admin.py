from django.contrib import admin

from .models import (
    Fornecedor,
    ItemPedidoCompra,
    PedidoCompra,
    ItemRecebimentoCompra,
    RecebimentoCompra,
)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = [
        'razao_social',
        'nome_fantasia',
        'cnpj',
        'matriz',
        'status',
        'atualizado_em',
    ]

    list_filter = [
        'status',
        'matriz',
    ]

    search_fields = [
        'razao_social',
        'nome_fantasia',
        'cnpj',
        'email',
    ]

    readonly_fields = [
        'uuid',
        'criado_em',
        'atualizado_em',
    ]


class ItemPedidoCompraInline(admin.TabularInline):
    model = ItemPedidoCompra
    extra = 0
    readonly_fields = [
        'quantidade_recebida',
    ]


@admin.register(PedidoCompra)
class PedidoCompraAdmin(admin.ModelAdmin):
    list_display = [
        'numero',
        'matriz',
        'fornecedor',
        'data_emissao',
        'previsao_entrega',
        'status',
        'criado_por',
    ]

    list_filter = [
        'status',
        'matriz',
        'data_emissao',
    ]

    search_fields = [
        'numero',
        'fornecedor__razao_social',
        'fornecedor__nome_fantasia',
        'fornecedor__cnpj',
    ]

    readonly_fields = [
        'uuid',
        'numero',
        'criado_em',
        'atualizado_em',
        'enviado_em',
        'cancelado_em',
    ]

    inlines = [
        ItemPedidoCompraInline,
    ]

class ItemRecebimentoCompraInline(admin.TabularInline):
    model = ItemRecebimentoCompra
    extra = 0
    can_delete = False
    readonly_fields = [
        'item_pedido',
        'quantidade',
        'movimentacao_estoque',
        'criado_em',
    ]


@admin.register(RecebimentoCompra)
class RecebimentoCompraAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'pedido',
        'loja',
        'documento_referencia',
        'recebido_por',
        'recebido_em',
    ]
    list_filter = [
        'matriz',
        'loja',
        'recebido_em',
    ]
    readonly_fields = [
        'uuid',
        'matriz',
        'loja',
        'pedido',
        'chave_idempotencia',
        'documento_referencia',
        'observacoes',
        'recebido_por',
        'recebido_em',
    ]
    inlines = [ItemRecebimentoCompraInline]
