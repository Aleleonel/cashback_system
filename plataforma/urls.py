from django.urls import path

from .views import (
    painel_master,
    lista_matrizes,
    criar_matriz,
    editar_matriz,
    alternar_status_matriz,
    lista_lojas,
    nova_empresa_matriz,
    nova_empresa_loja,
    nova_empresa_admin,
    nova_empresa_revisao,
    criar_loja,
    editar_loja,
    alternar_status_loja,
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

    path(
        'painel-master/lojas/nova/',
        criar_loja,
        name='criar_loja'
    ),

    path(
        'painel-master/lojas/<int:loja_id>/editar/',
        editar_loja,
        name='editar_loja'
    ),

    path(
        'painel-master/lojas/<int:loja_id>/status/',
        alternar_status_loja,
        name='alternar_status_loja'
    ),

    path(
        'painel-master/nova-empresa/',
        nova_empresa_matriz,
        name='nova_empresa_matriz'
    ),

    path(
        'painel-master/nova-empresa/loja/',
        nova_empresa_loja,
        name='nova_empresa_loja'
    ),

    path(
        'painel-master/nova-empresa/admin/',
        nova_empresa_admin,
        name='nova_empresa_admin'
    ),

    path(
        'painel-master/nova-empresa/revisao/',
        nova_empresa_revisao,
        name='nova_empresa_revisao'
    ),
]