from django.contrib import admin

from .models import ConfiguracaoComercial


@admin.register(ConfiguracaoComercial)
class ConfiguracaoComercialAdmin(admin.ModelAdmin):
    list_display = (
        "matriz",
        "atacado_ativo",
        "pedido_minimo_atacado",
        "desconto_atacado_percentual",
        "cashback_ativo",
        "voucher_ativo",
        "atualizada_em",
    )
    list_filter = (
        "atacado_ativo",
        "cashback_ativo",
        "voucher_ativo",
        "promocoes_ativas",
        "brindes_ativos",
    )
    search_fields = ("matriz__nome",)
    readonly_fields = ("criada_em", "atualizada_em")
