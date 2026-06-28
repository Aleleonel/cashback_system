from django.urls import path

from .views import (
    painel_master,
    lista_matrizes,
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
]