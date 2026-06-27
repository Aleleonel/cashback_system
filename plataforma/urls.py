from django.urls import path

from .views import painel_master


app_name = 'plataforma'


urlpatterns = [
    path(
        'painel-master/',
        painel_master,
        name='painel_master'
    ),
]