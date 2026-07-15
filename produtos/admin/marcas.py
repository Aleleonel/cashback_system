from django.contrib import admin

from produtos.models import Marca


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'fabricante',
        'matriz',
        'ativa',
        'criada_em',
    )

    list_filter = (
        'ativa',
        'matriz',
    )

    search_fields = (
        'nome',
        'fabricante',
    )

    ordering = (
        'nome',
    )

    readonly_fields = (
        'criada_em',
        'atualizada_em',
    )
