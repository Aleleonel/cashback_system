from django.contrib import admin

from fiscal.models_documento_fiscal import (
    DocumentoFiscal,
    SequenciaDocumentoFiscal,
)


@admin.register(DocumentoFiscal)
class DocumentoFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "modelo",
        "ambiente",
        "serie",
        "numero",
        "status",
        "loja",
        "criado_em",
    )
    list_filter = (
        "modelo",
        "ambiente",
        "status",
    )
    search_fields = (
        "chave_acesso",
        "protocolo_autorizacao",
        "idempotency_key",
    )
    readonly_fields = (
        "uuid",
        "criado_em",
        "atualizado_em",
    )


@admin.register(SequenciaDocumentoFiscal)
class SequenciaDocumentoFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "loja",
        "modelo",
        "ambiente",
        "serie",
        "proximo_numero",
        "atualizado_em",
    )
    list_filter = (
        "modelo",
        "ambiente",
    )