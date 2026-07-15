from django.contrib import admin

from produtos.models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
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
        'descricao',
    )

    ordering = (
        'nome',
    )

    readonly_fields = (
        'criada_em',
        'atualizada_em',
    )
