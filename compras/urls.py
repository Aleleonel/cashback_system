from django.urls import path

from . import views


app_name = 'compras'


urlpatterns = [
    path(
        'fornecedores/',
        views.listar_fornecedores,
        name='listar_fornecedores',
    ),
    path(
        'fornecedores/novo/',
        views.criar_fornecedor_view,
        name='criar_fornecedor',
    ),
    path(
        'fornecedores/<uuid:fornecedor_uuid>/editar/',
        views.editar_fornecedor_view,
        name='editar_fornecedor',
    ),
]