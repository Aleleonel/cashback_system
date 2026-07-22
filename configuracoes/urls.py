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
]
