from django.urls import path

from .views import dashboard, relatorio_clientes


app_name = 'relatorios'

urlpatterns = [
    path('cadastros/clientes/', relatorio_clientes, name='clientes'),
    path('cadastros/aniversariantes/', dashboard, name='aniversariantes'),
]
