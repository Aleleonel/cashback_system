from django.urls import path

from . import views


app_name = "configuracoes"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("caixa-pagamentos/formas/", views.formas_pagamento, name="formas_pagamento"),
    path("caixa-pagamentos/formas/nova/", views.forma_pagamento_criar, name="forma_pagamento_criar"),
    path("caixa-pagamentos/formas/<int:pk>/editar/", views.forma_pagamento_editar, name="forma_pagamento_editar"),
    path("empresa/", views.empresa, name="empresa"),
    path(
        "usuarios-permissoes/",
        views.usuarios_permissoes,
        name="usuarios_permissoes",
    ),
    path("criticas/", views.criticas, name="criticas"),
    path(
        "clientes-cashback/",
        views.clientes_cashback,
        name="clientes_cashback",
    ),
    path(
        "vendas-comissoes/",
        views.vendas_comissoes,
        name="vendas_comissoes",
    ),
    path(
        "vendas-comissoes/regras-comerciais/",
        views.regras_comerciais,
        name="regras_comerciais",
    ),
]
