from django.urls import path

from . import views
from . import views_csosn
from . import views_cst_icms


app_name = "fiscal"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path(
        "origens-mercadoria/",
        views.lista_origens_mercadoria,
        name="lista_origens_mercadoria",
    ),
    path(
        "origens-mercadoria/nova/",
        views.criar_origem_mercadoria_view,
        name="criar_origem_mercadoria",
    ),
    path(
        "origens-mercadoria/<int:origem_id>/editar/",
        views.editar_origem_mercadoria_view,
        name="editar_origem_mercadoria",
    ),
    path("cst-icms/", views_cst_icms.lista_csts_icms, name="lista_csts_icms"),
    path("cst-icms/novo/", views_cst_icms.criar_cst_icms_view, name="criar_cst_icms"),
    path("cst-icms/<int:cst_id>/editar/", views_cst_icms.editar_cst_icms_view, name="editar_cst_icms"),
    path("csosn/", views_csosn.lista_csosns, name="lista_csosns"),
    path("csosn/novo/", views_csosn.criar_csosn_view, name="criar_csosn"),
    path("csosn/<int:csosn_id>/editar/", views_csosn.editar_csosn_view, name="editar_csosn"),
]
