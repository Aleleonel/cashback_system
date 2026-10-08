from django.urls import path

from .views import dashboard, relatorio_clientes, relatorio_aniversariantes


app_name = 'relatorios'

urlpatterns = [
    path('cadastros/clientes/', relatorio_clientes, name='clientes'),
    path('cadastros/aniversariantes/', relatorio_aniversariantes, name='aniversariantes'),
]
