from django.contrib import admin

from produtos.models import UnidadeMedida


@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = (
        'sigla',
        'descricao',
        'matriz',
        'ativa',
    )

    list_filter = (
        'ativa',
        'matriz',
    )

    search_fields = (
        'sigla',
        'descricao',
    )

    ordering = (
        'sigla',
    )

    readonly_fields = (
        'criada_em',
        'atualizada_em',
    )
