from django.urls import path

from .views import (
    simular_beneficios_view,
    validar_voucher_view,
)


app_name = 'beneficios'


urlpatterns = [
    path(
        'simular/',
        simular_beneficios_view,
        name='simular'
    ),

    path(
        'validar-voucher/',
        validar_voucher_view,
        name='validar_voucher'
    ),
]