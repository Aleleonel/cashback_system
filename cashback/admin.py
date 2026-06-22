from django.contrib import admin

from .models import ConfiguracaoCashback, LancamentoCashback


@admin.register(ConfiguracaoCashback)
class ConfiguracaoCashbackAdmin(admin.ModelAdmin):
    list_display = (
        'loja',
        'percentual_cashback',
        'dias_para_liberar',
        'dias_para_expirar',
        'envio_email_saldo',
    )


@admin.register(LancamentoCashback)
class LancamentoCashbackAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'loja',
        'valor_compra',
        'valor_cashback',
        'data_compra',
        'data_liberacao',
        'data_expiracao',
        'status',
    )

    search_fields = (
        'cliente__nome',
        'cliente__cpf',
    )

    list_filter = (
        'loja',
        'status',
        'data_compra',
    )