from django.urls import path

from . import views


app_name = "pdv"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("caixa/abrir/", views.abrir_caixa, name="abrir_caixa"),
    path(
        "caixa/abrir/confirmar/",
        views.confirmar_abertura_caixa,
        name="confirmar_abertura_caixa",
    ),
    path("api/estado/", views.estado_venda, name="estado_venda"),
    path("api/clientes/", views.buscar_clientes, name="buscar_clientes"),
    path("api/clientes/selecionar/", views.selecionar_cliente, name="selecionar_cliente"),
    path("api/vendedores/", views.buscar_vendedores, name="buscar_vendedores"),
    path("api/vendedores/selecionar/", views.selecionar_vendedor, name="selecionar_vendedor"),
    path("api/produtos/", views.buscar_produtos, name="buscar_produtos"),
    path("api/itens/adicionar/", views.adicionar_item, name="adicionar_item"),
    path("api/itens/<int:item_id>/alterar/", views.alterar_item, name="alterar_item"),
    path("api/itens/<int:item_id>/cancelar/", views.cancelar_item, name="cancelar_item"),
]
