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
    path(
        'pedidos/',
        views.listar_pedidos_compra,
        name='listar_pedidos_compra',
    ),
    path(
        'pedidos/novo/',
        views.criar_pedido_compra_view,
        name='criar_pedido_compra',
    ),
    path(
        'pedidos/<uuid:pedido_uuid>/',
        views.detalhar_pedido_compra,
        name='detalhar_pedido_compra',
    ),
    path(
        'pedidos/<uuid:pedido_uuid>/editar/',
        views.editar_pedido_compra_view,
        name='editar_pedido_compra',
    ),
    path(
        'pedidos/<uuid:pedido_uuid>/itens/adicionar/',
        views.adicionar_item_pedido_compra_view,
        name='adicionar_item_pedido_compra',
    ),
    path(
        'pedidos/<uuid:pedido_uuid>/itens/<int:item_id>/remover/',
        views.remover_item_pedido_compra_view,
        name='remover_item_pedido_compra',
    ),
    path(
        'pedidos/<uuid:pedido_uuid>/enviar/',
        views.enviar_pedido_compra_view,
        name='enviar_pedido_compra',
    ),
    path(
        'pedidos/<uuid:pedido_uuid>/cancelar/',
        views.cancelar_pedido_compra_view,
        name='cancelar_pedido_compra',
    ),
]