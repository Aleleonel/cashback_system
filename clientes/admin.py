from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'cpf',
        'telefone',
        'email',
        'matriz',
        'loja_cadastro',
        'aceita_email',
        'aceita_sms',
        'ativo',
    )

    search_fields = (
        'nome',
        'cpf',
        'telefone',
        'email',
    )

    list_filter = (
        'matriz',
        'loja_cadastro',
        'ativo',
        'aceita_email',
        'aceita_sms',
    )