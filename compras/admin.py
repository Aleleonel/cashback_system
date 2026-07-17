from django.contrib import admin

from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = [
        'razao_social',
        'nome_fantasia',
        'cnpj',
        'matriz',
        'status',
        'atualizado_em',
    ]

    list_filter = [
        'status',
        'matriz',
    ]

    search_fields = [
        'razao_social',
        'nome_fantasia',
        'cnpj',
        'email',
    ]

    readonly_fields = [
        'uuid',
        'criado_em',
        'atualizado_em',
    ]

    ordering = [
        'razao_social',
    ]