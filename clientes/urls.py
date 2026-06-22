from django.urls import path

from .views import buscar_cliente_cpf

app_name = 'clientes'

urlpatterns = [
    path(
        'buscar-cpf/',
        buscar_cliente_cpf,
        name='buscar_cliente_cpf'
    ),
]