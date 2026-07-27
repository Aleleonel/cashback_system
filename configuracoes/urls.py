from django.urls import path

from . import views


app_name = "configuracoes"

urlpatterns = [
    path("", views.inicio, name="inicio"),
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
