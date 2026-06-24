from django.urls import path

from .views import (
    aniversariantes_mes,
    disparar_aniversariantes,
    reenviar_aniversariante,
    historico_envios,
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

    path(
        'aniversariantes/<int:cliente_id>/reenviar/',
        reenviar_aniversariante,
        name='reenviar_aniversariante'
    ),

    path(
        'historico/',
        historico_envios,
        name='historico_envios'
    ),
]