from django.urls import path

from .views import (
    auditoria_empresa,
    dashboard_empresa,
    lista_lojas_empresa,
    criar_loja_empresa_view,
    editar_loja_empresa_view,
    alternar_status_loja_empresa_view,
    configurar_cashback_empresa,
)

app_name = 'empresa'


urlpatterns = [
    path(
        '',
        dashboard_empresa,
        name='dashboard'
    ),

    path(
        'auditoria/',
        auditoria_empresa,
        name='auditoria'
    ),
    path(
        'lojas/',
        lista_lojas_empresa,
        name='lista_lojas'
    ),

    path(
        'lojas/nova/',
        criar_loja_empresa_view,
        name='criar_loja'
    ),

    path(
        'lojas/<int:loja_id>/editar/',
        editar_loja_empresa_view,
        name='editar_loja'
    ),

    path(
        'lojas/<int:loja_id>/status/',
        alternar_status_loja_empresa_view,
        name='alternar_status_loja'
    ),

    path(
        'configuracoes/cashback/',
        configurar_cashback_empresa,
        name='configurar_cashback'
    ),
]