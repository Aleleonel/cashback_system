from django.contrib import admin

from fiscal.models import OrigemMercadoria


@admin.register(OrigemMercadoria)
class OrigemMercadoriaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao",
        "ativo",
        "atualizado_em",
    )
    list_filter = ("ativo",)
    search_fields = (
        "codigo",
        "descricao",
    )
    ordering = ("codigo",)
    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))

        if obj is not None:
            fields.append("codigo")

        return tuple(fields)

from fiscal.models import CSTICMS

@admin.register(CSTICMS)
class CSTICMSAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao", "exige_aliquota", "permite_reducao_base", "permite_diferimento", "permite_substituicao_tributaria", "ativo", "atualizado_em")
    list_filter = ("ativo", "exige_aliquota", "permite_reducao_base", "permite_diferimento", "permite_substituicao_tributaria")
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = ("criado_em", "atualizado_em")
    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import CSOSN

@admin.register(CSOSN)
class CSOSNAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao", "exige_aliquota", "permite_reducao_base", "permite_credito", "permite_substituicao_tributaria", "ativo", "atualizado_em")
    list_filter = ("ativo", "exige_aliquota", "permite_reducao_base", "permite_credito", "permite_substituicao_tributaria")
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = ("criado_em", "atualizado_em")
    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)
