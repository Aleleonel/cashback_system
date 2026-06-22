from django.contrib import admin

from .models import LancamentoCashback, UsoCashback


@admin.register(LancamentoCashback)
class LancamentoCashbackAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'matriz',
        'loja',
        'valor_compra',
        'percentual_cashback',
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
        'matriz',
        'loja',
        'status',
        'data_compra',
    )


@admin.register(UsoCashback)
class UsoCashbackAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'matriz',
        'loja',
        'valor_usado',
        'data_uso',
    )

    search_fields = (
        'cliente__nome',
        'cliente__cpf',
    )

    list_filter = (
        'matriz',
        'loja',
        'data_uso',
    )