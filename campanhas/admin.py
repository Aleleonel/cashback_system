from django.contrib import admin

from .models import CampanhaAniversarioEnvio


@admin.register(CampanhaAniversarioEnvio)
class CampanhaAniversarioEnvioAdmin(admin.ModelAdmin):
    list_display = (
        'cliente',
        'matriz',
        'canal',
        'status',
        'criado_em',
        'enviado_em',
    )

    search_fields = (
        'cliente__nome',
        'cliente__cpf',
        'mensagem',
    )

    list_filter = (
        'matriz',
        'canal',
        'status',
        'criado_em',
    )