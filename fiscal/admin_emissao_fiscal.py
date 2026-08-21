from django.contrib import admin

from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja


@admin.register(ConfiguracaoEmissaoFiscalLoja)
class ConfiguracaoEmissaoFiscalLojaAdmin(admin.ModelAdmin):
    list_display = (
        "loja",
        "razao_social",
        "inscricao_estadual",
        "uf",
        "ambiente_nfce",
        "serie_nfce",
        "ativa",
    )
    list_filter = ("ambiente_nfce", "uf", "ativa")
    search_fields = (
        "loja__nome",
        "loja__cnpj",
        "razao_social",
        "nome_fantasia",
        "inscricao_estadual",
    )
