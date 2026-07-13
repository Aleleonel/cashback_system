from django.contrib import admin

from produtos.models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_interno',
        'nome',
        'matriz',
        'categoria',
        'marca',
        'preco_venda',
        'status',
        'controla_estoque',
    )

    list_filter = (
        'status',
        'controla_estoque',
        'origem_preco',
        'matriz',
        'categoria',
        'marca',
    )

    search_fields = (
        'codigo_interno',
        'sku',
        'gtin',
        'nome',
        'descricao',
    )

    ordering = (
        'nome',
    )

    autocomplete_fields = (
        'matriz',
        'categoria',
        'marca',
        'unidade_medida',
    )

    readonly_fields = (
        'uuid',
        'lucro_bruto_unitario',
        'markup_percentual',
        'margem_bruta_percentual',
        'criado_em',
        'atualizado_em',
    )

    fieldsets = (
        (
            'Identificação',
            {
                'fields': (
                    'uuid',
                    'matriz',
                    'codigo_interno',
                    'sku',
                    'gtin',
                    'ncm',
                    'nome',
                    'descricao',
                )
            },
        ),
        (
            'Classificação',
            {
                'fields': (
                    'categoria',
                    'marca',
                    'unidade_medida',
                    'status',
                )
            },
        ),
        (
            'Preço',
            {
                'fields': (
                    'custo_base',
                    'preco_venda',
                    'origem_preco',
                    'lucro_bruto_unitario',
                    'markup_percentual',
                    'margem_bruta_percentual',
                )
            },
        ),
        (
            'Logística',
            {
                'fields': (
                    'peso_liquido_gramas',
                    'peso_bruto_gramas',
                    'altura_cm',
                    'largura_cm',
                    'comprimento_cm',
                )
            },
        ),
        (
            'Estoque',
            {
                'fields': (
                    'controla_estoque',
                    'estoque_minimo',
                )
            },
        ),
        (
            'Auditoria',
            {
                'fields': (
                    'criado_em',
                    'atualizado_em',
                )
            },
        ),
    )
