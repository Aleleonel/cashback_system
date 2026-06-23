from django.contrib import admin

from .models import ConfiguracaoSistema


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):

    list_display = (
        'matriz',
        'percentual_cashback',
        'dias_liberacao',
        'dias_expiracao',
        'valor_minimo_compra',
    )