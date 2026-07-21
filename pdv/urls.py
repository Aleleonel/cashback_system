from django.urls import path

from . import views


app_name = "pdv"

urlpatterns = [
    path("", views.inicio, name="inicio"),
]
