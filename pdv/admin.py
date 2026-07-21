from django.contrib import admin

from .models import (
    Caixa,
    FormaPagamento,
    MovimentacaoCaixa,
    PagamentoVenda,
    SessaoCaixa,
    Venda,
)


@admin.register(Caixa)
class CaixaAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "loja", "status")
    list_filter = ("status", "matriz", "loja")
    search_fields = ("nome", "codigo", "loja__nome")


@admin.register(SessaoCaixa)
class SessaoCaixaAdmin(admin.ModelAdmin):
    list_display = (
        "caixa",
        "operador_abertura",
        "status",
        "valor_abertura",
        "aberta_em",
        "fechada_em",
    )
    list_filter = ("status", "caixa__loja")
    search_fields = ("caixa__nome", "operador_abertura__username")
    readonly_fields = ("aberta_em",)


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "codigo",
        "tipo",
        "matriz",
        "ativa",
        "permite_parcelamento",
        "gera_contas_receber",
        "somente_funcionario",
    )
    list_filter = (
        "ativa",
        "tipo",
        "permite_parcelamento",
        "gera_contas_receber",
        "somente_funcionario",
    )
    search_fields = ("nome", "codigo")


class PagamentoVendaInline(admin.TabularInline):
    model = PagamentoVenda
    extra = 0


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "loja",
        "cliente",
        "tipo_operacao",
        "status",
        "modalidade",
        "total",
        "criada_em",
    )
    list_filter = ("status", "tipo_operacao", "modalidade", "loja")
    search_fields = ("numero", "cliente__nome", "cliente__cpf")
    readonly_fields = ("criada_em", "atualizada_em")
    inlines = [PagamentoVendaInline]


@admin.register(PagamentoVenda)
class PagamentoVendaAdmin(admin.ModelAdmin):
    list_display = (
        "venda",
        "forma_pagamento",
        "valor",
        "parcelas",
        "troco",
        "criado_em",
    )
    list_filter = ("forma_pagamento",)
    search_fields = ("venda__numero", "referencia_externa")


@admin.register(MovimentacaoCaixa)
class MovimentacaoCaixaAdmin(admin.ModelAdmin):
    list_display = (
        "sessao_caixa",
        "tipo",
        "valor",
        "operador",
        "venda",
        "criada_em",
    )
    list_filter = ("tipo", "sessao_caixa__caixa")
    search_fields = ("descricao", "venda__numero")
    readonly_fields = (
        "sessao_caixa",
        "tipo",
        "valor",
        "operador",
        "venda",
        "movimentacao_estornada",
        "descricao",
        "criada_em",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
