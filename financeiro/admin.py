from django.contrib import admin

from .models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro


class ParcelaFinanceiraInline(admin.TabularInline):
    model = ParcelaFinanceira
    extra = 0
    can_delete = False
    fields = ("numero", "vencimento", "valor_original", "status", "criado_em")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class BaixaFinanceiraInline(admin.TabularInline):
    model = BaixaFinanceira
    extra = 0
    can_delete = False
    fields = ("tipo", "valor", "data", "chave_idempotencia", "observacao", "criado_em")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TituloFinanceiro)
class TituloFinanceiroAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "matriz",
        "loja",
        "natureza",
        "origem_tipo",
        "descricao",
        "valor_original",
        "status",
        "data_emissao",
    )
    list_filter = ("natureza", "status", "origem_tipo", "matriz", "loja", "data_emissao")
    search_fields = ("uuid", "origem_id", "chave_idempotencia", "descricao")
    readonly_fields = (
        "uuid",
        "matriz",
        "loja",
        "natureza",
        "origem_tipo",
        "origem_id",
        "chave_idempotencia",
        "descricao",
        "valor_original",
        "status",
        "data_emissao",
        "criado_em",
        "atualizado_em",
    )
    inlines = [ParcelaFinanceiraInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ParcelaFinanceira)
class ParcelaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("titulo", "numero", "vencimento", "valor_original", "status")
    list_filter = ("status", "vencimento", "titulo__natureza", "titulo__matriz", "titulo__loja")
    search_fields = ("titulo__uuid", "titulo__origem_id", "titulo__descricao")
    readonly_fields = (
        "titulo",
        "numero",
        "vencimento",
        "valor_original",
        "status",
        "criado_em",
    )
    inlines = [BaixaFinanceiraInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BaixaFinanceira)
class BaixaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("parcela", "tipo", "valor", "data", "chave_idempotencia", "criado_em")
    list_filter = ("tipo", "data", "parcela__titulo__natureza", "parcela__titulo__matriz", "parcela__titulo__loja")
    search_fields = (
        "chave_idempotencia",
        "observacao",
        "parcela__titulo__uuid",
        "parcela__titulo__origem_id",
    )
    readonly_fields = (
        "parcela",
        "valor",
        "data",
        "tipo",
        "chave_idempotencia",
        "observacao",
        "criado_em",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False