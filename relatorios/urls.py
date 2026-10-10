from django.urls import path

from .views import dashboard, hub_cadastros, hub_vendas, hub_estoque, hub_financeiro, relatorio_clientes, relatorio_aniversariantes
from financeiro.views import painel_relatorio


app_name = 'relatorios'

urlpatterns = [
    path('cadastros/', hub_cadastros, name='cadastros'),
    path('vendas/', hub_vendas, name='vendas'),
    path('estoque/', hub_estoque, name='estoque'),
    path('financeiro/', hub_financeiro, name='financeiro'),
    path('financeiro/painel/', painel_relatorio, name='financeiro_painel'),
    path('cadastros/clientes/', relatorio_clientes, name='clientes'),
    path('cadastros/aniversariantes/', relatorio_aniversariantes, name='aniversariantes'),
]
