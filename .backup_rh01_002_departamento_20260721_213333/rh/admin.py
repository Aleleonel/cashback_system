from django.contrib import admin

from .models import Cargo


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "matriz",
        "ativo",
        "criado_em",
    )

    list_filter = (
        "ativo",
        "matriz",
    )

    search_fields = (
        "nome",
        "descricao",
    )

    ordering = (
        "nome",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "matriz",
                    "nome",
                    "descricao",
                    "ativo",
                )
            },
        ),
        (
            "Auditoria",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "criado_em",
                    "atualizado_em",
                ),
            },
        ),
    )