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

from fiscal.models import CFOP


@admin.register(CFOP)
class CFOPAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao",
        "tipo_operacao",
        "destino_operacao",
        "gera_movimento_estoque",
        "permite_devolucao",
        "permite_remessa",
        "ativo",
        "atualizado_em",
    )
    list_filter = (
        "ativo",
        "tipo_operacao",
        "destino_operacao",
        "gera_movimento_estoque",
        "permite_devolucao",
        "permite_remessa",
    )
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = (
        "tipo_operacao",
        "destino_operacao",
        "criado_em",
        "atualizado_em",
    )

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import NCM


@admin.register(NCM)
class NCMAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao_resumida",
        "unidade_tributavel_padrao",
        "ativo",
        "atualizado_em",
    )
    list_filter = ("ativo",)
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = ("criado_em", "atualizado_em")
    list_per_page = 50

    @admin.display(description="Descricao")
    def descricao_resumida(self, obj):
        if len(obj.descricao) <= 100:
            return obj.descricao

        return f"{obj.descricao[:97]}..."

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))

        if obj is not None:
            fields.append("codigo")

        return tuple(fields)

from fiscal.models import CSTPIS


@admin.register(CSTPIS)
class CSTPISAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao",
        "tipo_operacao",
        "tributado",
        "exige_aliquota",
        "permite_credito",
        "exige_base_calculo",
        "ativo",
    )
    list_filter = (
        "ativo",
        "tipo_operacao",
        "tributado",
        "exige_aliquota",
        "permite_credito",
        "exige_base_calculo",
    )
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = ("criado_em", "atualizado_em")
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import CSTCOFINS


@admin.register(CSTCOFINS)
class CSTCOFINSAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao",
        "tipo_operacao",
        "tributado",
        "exige_aliquota",
        "permite_credito",
        "exige_base_calculo",
        "ativo",
    )
    list_filter = (
        "ativo",
        "tipo_operacao",
        "tributado",
        "exige_aliquota",
        "permite_credito",
        "exige_base_calculo",
    )
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = ("criado_em", "atualizado_em")
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import CSTIPI


@admin.register(CSTIPI)
class CSTIPIAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao",
        "tipo_operacao",
        "tributado",
        "exige_aliquota",
        "permite_credito",
        "exige_base_calculo",
        "exige_codigo_enquadramento",
        "ativo",
    )
    list_filter = (
        "ativo",
        "tipo_operacao",
        "tributado",
        "exige_aliquota",
        "permite_credito",
        "exige_base_calculo",
        "exige_codigo_enquadramento",
    )
    search_fields = ("codigo", "descricao")
    ordering = ("codigo",)
    readonly_fields = ("criado_em", "atualizado_em")
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import CEST


@admin.register(CEST)
class CESTAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_formatado",
        "descricao_resumida",
        "segmento",
        "ncm_referencia",
        "versao_tabela",
        "ativo",
        "atualizado_em",
    )
    list_filter = (
        "ativo",
        "segmento",
        "versao_tabela",
    )
    search_fields = (
        "codigo",
        "descricao",
        "segmento",
        "ncm_referencia",
        "excecao",
    )
    ordering = ("codigo",)
    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )
    list_per_page = 50

    @admin.display(description="Codigo")
    def codigo_formatado(self, obj):
        return obj.codigo_formatado

    @admin.display(description="Descricao")
    def descricao_resumida(self, obj):
        if len(obj.descricao) <= 100:
            return obj.descricao
        return f"{obj.descricao[:97]}..."

    def get_readonly_fields(self, request, obj=None):
        fields = list(
            super().get_readonly_fields(request, obj)
        )
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import BeneficioFiscal


@admin.register(BeneficioFiscal)
class BeneficioFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "descricao_resumida",
        "uf",
        "tipo_beneficio",
        "regime_tributario",
        "percentual_reducao",
        "percentual_credito",
        "ativo",
        "atualizado_em",
    )
    list_filter = (
        "ativo",
        "uf",
        "tipo_beneficio",
        "regime_tributario",
        "exige_motivo_desoneracao",
    )
    search_fields = (
        "codigo",
        "descricao",
        "fundamento_legal",
    )
    ordering = ("codigo",)
    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )
    list_per_page = 50

    @admin.display(description="Descricao")
    def descricao_resumida(self, obj):
        if len(obj.descricao) <= 100:
            return obj.descricao
        return f"{obj.descricao[:97]}..."

    def get_readonly_fields(self, request, obj=None):
        fields = list(
            super().get_readonly_fields(request, obj)
        )
        if obj is not None:
            fields.append("codigo")
        return tuple(fields)

from fiscal.models import RegraFiscal


@admin.register(RegraFiscal)
class RegraFiscalAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_interno",
        "nome",
        "prioridade",
        "matriz",
        "loja",
        "regime_tributario",
        "tipo_operacao",
        "finalidade_operacao",
        "ativo",
    )
    list_filter = (
        "ativo",
        "regime_tributario",
        "tipo_operacao",
        "finalidade_operacao",
        "uf_origem",
        "uf_destino",
    )
    search_fields = (
        "codigo_interno",
        "nome",
        "descricao",
    )
    ordering = (
        "prioridade",
        "codigo_interno",
    )
    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )
    list_per_page = 50

    def get_readonly_fields(self, request, obj=None):
        fields = list(
            super().get_readonly_fields(request, obj)
        )
        if obj is not None:
            fields.append("codigo_interno")
        return tuple(fields)

from fiscal import admin_configuracao_fiscal  # noqa: F401
