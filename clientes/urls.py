from django.urls import path

from .views import (
    buscar_cliente_cpf,
    criar_cliente,
    editar_cliente,
    extrato_cliente,
    lista_clientes,
    importar_clientes,
    confirmar_importacao_clientes,
)

app_name = 'clientes'

urlpatterns = [

    path(
        '', 
        lista_clientes, 
        name='lista_clientes'
    ),

    path(
        'novo/', 
        criar_cliente, 
        name='criar_cliente'
    ),

    path(
        'importar/',
        importar_clientes, 
        name='importar_clientes'
    ),

    path(
        'importar/confirmar/',
        confirmar_importacao_clientes,
        name='confirmar_importacao_clientes'
    ),

    path(
        '<int:cliente_id>/editar/',
        editar_cliente,
        name='editar_cliente'
    ),

    path(
        'extrato/<int:cliente_id>/',
        extrato_cliente,
        name='extrato_cliente'
    ),

    path(
        'buscar-cpf/',
        buscar_cliente_cpf,
        name='buscar_cliente_cpf'
    ),

]