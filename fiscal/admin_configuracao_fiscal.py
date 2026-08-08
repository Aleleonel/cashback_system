from django.contrib import admin

from fiscal.models_configuracao_fiscal import ConfiguracaoFiscalMatriz


@admin.register(ConfiguracaoFiscalMatriz)
class ConfiguracaoFiscalMatrizAdmin(admin.ModelAdmin):
    list_display = (
        "matriz",
        "regime_tributario",
        "uf_origem",
        "contribuinte_icms",
        "consumidor_final_padrao",
        "ativa",
        "atualizado_em",
    )
    list_filter = (
        "regime_tributario",
        "uf_origem",
        "contribuinte_icms",
        "ativa",
    )
    search_fields = ("matriz__nome", "matriz__cnpj")
    readonly_fields = ("criado_em", "atualizado_em")
    list_select_related = ("matriz",)
