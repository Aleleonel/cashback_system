from django.contrib import admin

from .models import (
    CampanhaAniversarioEnvio,
    ConfiguracaoCampanhaAniversario,
    TemplateCampanha,
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


@admin.register(TemplateCampanha)
class TemplateCampanhaAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'matriz',
        'tipo',
        'canal',
        'ativo',
        'atualizado_em',
    )

    list_filter = (
        'matriz',
        'tipo',
        'canal',
        'ativo',
    )

    search_fields = (
        'nome',
        'assunto',
        'mensagem',
        'matriz__nome',
    )