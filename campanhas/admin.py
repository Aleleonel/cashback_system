from django.contrib import admin

from .models import (
    CampanhaAniversarioEnvio,
    ConfiguracaoCampanhaAniversario,
)


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

@admin.register(ConfiguracaoCampanhaAniversario)
class ConfiguracaoCampanhaAniversarioAdmin(admin.ModelAdmin):

    list_display = (
        'matriz',
        'ativa',
        'canal_padrao',
        'atualizado_em',
    )

    list_filter = (
        'ativa',
        'canal_padrao',
    )

    search_fields = (
        'matriz__nome',
        'assunto_padrao',
    )