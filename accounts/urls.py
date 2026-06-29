from django.urls import path

from .views import (
    lista_usuarios,
    criar_usuario,
    editar_usuario,
    alternar_status_usuario,
)

app_name = 'accounts'


urlpatterns = [
    path(
        'painel-master/usuarios/',
        lista_usuarios,
        name='lista_usuarios'
    ),

    path(
        'painel-master/usuarios/novo/',
        criar_usuario,
        name='criar_usuario'
    ),

    path(
        'painel-master/usuarios/<int:usuario_id>/editar/',
        editar_usuario,
        name='editar_usuario'
    ),

    path(
        'painel-master/usuarios/<int:usuario_id>/status/',
        alternar_status_usuario,
        name='alternar_status_usuario'
    ),
]