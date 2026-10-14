from django.urls import path

from .views import dashboard, hub_cadastros, hub_vendas, hub_estoque, hub_financeiro, hub_vouchers, relatorio_utilizacao_vouchers, relatorio_clientes, relatorio_aniversariantes, hub_cashback, relatorio_movimentacoes_cashback
from financeiro.views import painel_relatorio


app_name = 'relatorios'

urlpatterns = [
    path('cashback/', hub_cashback, name='cashback'),
    path('cashback/movimentacoes/', relatorio_movimentacoes_cashback, name='cashback_movimentacoes'),
    path('cadastros/', hub_cadastros, name='cadastros'),
    path('vendas/', hub_vendas, name='vendas'),
    path('estoque/', hub_estoque, name='estoque'),
    path('financeiro/', hub_financeiro, name='financeiro'),
    path('financeiro/painel/', painel_relatorio, name='financeiro_painel'),
    path('vouchers/', hub_vouchers, name='vouchers'),
    path('vouchers/utilizacoes/', relatorio_utilizacao_vouchers, name='vouchers_utilizacoes'),
    path('cadastros/clientes/', relatorio_clientes, name='clientes'),
    path('cadastros/aniversariantes/', relatorio_aniversariantes, name='aniversariantes'),
]
