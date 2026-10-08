from django.urls import path

from .views import dashboard, hub_cadastros, relatorio_clientes, relatorio_aniversariantes


app_name = 'relatorios'

urlpatterns = [
    path('cadastros/', hub_cadastros, name='cadastros'),
    path('cadastros/clientes/', relatorio_clientes, name='clientes'),
    path('cadastros/aniversariantes/', relatorio_aniversariantes, name='aniversariantes'),
]
