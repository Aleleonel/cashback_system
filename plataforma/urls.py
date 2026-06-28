from django.urls import path

from .views import (
    painel_master,
    lista_matrizes,
    criar_matriz,
    editar_matriz,
    alternar_status_matriz,
    lista_lojas,
)

app_name = 'plataforma'


urlpatterns = [
    path(
        'painel-master/',
        painel_master,
        name='painel_master'
    ),

    path(
        'painel-master/matrizes/',
        lista_matrizes,
        name='lista_matrizes'
    ),

    path(
        'painel-master/matrizes/nova/',
        criar_matriz,
        name='criar_matriz'
    ),

    path(
        'painel-master/matrizes/<int:matriz_id>/editar/',
        editar_matriz,
        name='editar_matriz'
    ),

    path(
        'painel-master/matrizes/<int:matriz_id>/status/',
        alternar_status_matriz,
        name='alternar_status_matriz'
    ),

    path(
        'painel-master/lojas/',
        lista_lojas,
        name='lista_lojas'
    ),
]