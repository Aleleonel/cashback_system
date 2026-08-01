from django.urls import path

from . import views


app_name = "pdv"

urlpatterns = [
    # PDV-04C.1 - ROTAS DE FECHAMENTO DE CAIXA
    path("caixa/fechar/", views.fechar_caixa, name="fechar_caixa"),
    path(
        "caixa/historico/",
        views.historico_fechamentos,
        name="historico_fechamentos",
    ),
    path(
        "caixa/fechar/confirmar/",
        views.confirmar_fechamento_caixa,
        name="confirmar_fechamento_caixa",
    ),
    path('venda/voucher/validar/', views.validar_voucher_venda_web, name='validar_voucher_venda'),
    path('venda/cancelar/', views.cancelar_venda_web, name='cancelar_venda'),

    path("", views.inicio, name="inicio"),
    path(
        "vendas/",
        views.historico_vendas,
        name="historico_vendas",
    ),
    path(
        "vendas/<uuid:venda_uuid>/cupom/",
        views.cupom_venda_nao_fiscal,
        name="cupom_venda_nao_fiscal",
    ),
    path(
        "vendas/<uuid:venda_uuid>/",
        views.detalhe_venda,
        name="detalhe_venda",
    ),
    path("caixa/abrir/", views.abrir_caixa, name="abrir_caixa"),
    path(
        "caixa/abrir/confirmar/",
        views.confirmar_abertura_caixa,
        name="confirmar_abertura_caixa",
    ),
    path("api/estado/", views.estado_venda, name="estado_venda"),
    path("api/fechamento/opcoes/", views.opcoes_fechamento, name="opcoes_fechamento"),
    path("api/clientes/", views.buscar_clientes, name="buscar_clientes"),
    path("api/clientes/selecionar/", views.selecionar_cliente, name="selecionar_cliente"),
    path("api/vendedores/", views.buscar_vendedores, name="buscar_vendedores"),
    path("api/vendedores/selecionar/", views.selecionar_vendedor, name="selecionar_vendedor"),
    path("api/produtos/", views.buscar_produtos, name="buscar_produtos"),
    path("api/itens/adicionar/", views.adicionar_item, name="adicionar_item"),
    path("api/itens/<int:item_id>/alterar/", views.alterar_item, name="alterar_item"),
    path("api/itens/<int:item_id>/cancelar/", views.cancelar_item, name="cancelar_item"),
    path("api/finalizar/", views.finalizar_venda_web, name="finalizar_venda"),
]
