from django.contrib import admin

from .models import (
    UsoVoucher,
    Voucher,
    VoucherLoja,
)


class VoucherLojaInline(admin.TabularInline):
    model = VoucherLoja
    extra = 0


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):

    list_display = (
        'codigo',
        'nome',
        'matriz',
        'tipo',
        'status',
        'data_inicio',
        'data_fim',
        'limite_utilizacao',
        'total_utilizado',
    )

    list_filter = (
        'status',
        'tipo',
        'origem',
        'matriz',
        'data_inicio',
        'data_fim',
    )

    search_fields = (
        'codigo',
        'nome',
        'descricao',
        'matriz__nome',
        'cliente__nome',
        'cliente__cpf',
    )

    inlines = [
        VoucherLojaInline,
    ]


@admin.register(UsoVoucher)
class UsoVoucherAdmin(admin.ModelAdmin):

    list_display = (
        'voucher',
        'cliente',
        'loja',
        'usuario',
        'valor_compra',
        'valor_desconto',
        'criado_em',
    )

    list_filter = (
        'matriz',
        'loja',
        'criado_em',
    )

    search_fields = (
        'voucher__codigo',
        'cliente__nome',
        'cliente__cpf',
        'usuario__username',
    )