from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):

    list_display = (
        'criado_em',
        'usuario',
        'matriz',
        'loja',
        'acao',
        'recurso',
        'recurso_id',
    )

    list_filter = (
        'acao',
        'matriz',
        'loja',
        'criado_em',
    )

    search_fields = (
        'usuario__username',
        'matriz__nome',
        'loja__nome',
        'recurso',
        'recurso_id',
        'descricao',
        'ip',
    )

    readonly_fields = (
        'uuid',
        'usuario',
        'matriz',
        'loja',
        'acao',
        'recurso',
        'recurso_id',
        'descricao',
        'ip',
        'user_agent',
        'criado_em',
    )