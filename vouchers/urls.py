from django.urls import path

from .views import (
    lista_vouchers,
    criar_voucher_view,
    editar_voucher_view,
    ativar_voucher_view,
    inativar_voucher_view,
)


app_name = 'vouchers'


urlpatterns = [
    path(
        '',
        lista_vouchers,
        name='lista_vouchers'
    ),

    path(
        'novo/',
        criar_voucher_view,
        name='criar_voucher'
    ),

    path(
        '<int:voucher_id>/editar/',
        editar_voucher_view,
        name='editar_voucher'
    ),

    path(
        '<int:voucher_id>/ativar/',
        ativar_voucher_view,
        name='ativar_voucher'
    ),

    path(
        '<int:voucher_id>/inativar/',
        inativar_voucher_view,
        name='inativar_voucher'
    ),
]