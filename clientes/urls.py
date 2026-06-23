from django.urls import path
from .views import (
    buscar_cliente_cpf,
    extrato_cliente,
    lista_clientes,
)

app_name = 'clientes'

urlpatterns = [
    path(
        'buscar-cpf/',
        buscar_cliente_cpf,
        name='buscar_cliente_cpf'
    ),

    path(
        'extrato/<int:cliente_id>/',
        extrato_cliente,
        name='extrato_cliente'
    ),

    path(
        '',
        lista_clientes,
        name='lista_clientes'
    ),
]