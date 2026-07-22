from django.urls import path

from . import views


app_name = "configuracoes"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("criticas/", views.criticas, name="criticas"),
]
