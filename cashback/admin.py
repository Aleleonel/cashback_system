from django.contrib import admin

from .models import LancamentoCashback, UsoCashback, UsoLancamentoCashback


@admin.register(LancamentoCashback)
class LancamentoCashbackAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'matriz',
        'loja',
        'valor_compra',
        'percentual_cashback',
        'valor_cashback',
        'valor_utilizado',
        'valor_restante_admin',
        'data_compra',
        'data_liberacao',
        'data_expiracao',
        'disponivel_admin',
    )

    search_fields = (
        'cliente__nome',
        'cliente__cpf',
    )

    list_filter = (
        'matriz',
        'loja',
        'data_compra',
        'data_liberacao',
        'data_expiracao',
    )

    def valor_restante_admin(self, obj):
        return obj.valor_restante

    valor_restante_admin.short_description = 'Valor restante'

    def disponivel_admin(self, obj):
        return obj.disponivel_para_uso

    disponivel_admin.boolean = True
    disponivel_admin.short_description = 'Disponível'


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


@admin.register(UsoLancamentoCashback)
class UsoLancamentoCashbackAdmin(admin.ModelAdmin):
    list_display = (
        'uso_cashback',
        'lancamento',
        'valor_utilizado',
        'criado_em',
    )