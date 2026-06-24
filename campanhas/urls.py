from django.urls import path

from .views import (
    aniversariantes_mes,
    disparar_aniversariantes,
)


app_name = 'campanhas'

urlpatterns = [
    path(
        'aniversariantes/',
        aniversariantes_mes,
        name='aniversariantes_mes'
    ),

    path(
        'aniversariantes/disparar/',
        disparar_aniversariantes,
        name='disparar_aniversariantes'
    ),
]