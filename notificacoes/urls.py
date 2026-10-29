from django.urls import path
from . import views

app_name = "notificacoes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/marcar-lida/", views.marcar_lida, name="marcar_lida"),
]
