from django.urls import path

from .views import dashboard, hub_cadastros, hub_vendas, hub_estoque, hub_financeiro, hub_vouchers, relatorio_utilizacao_vouchers, relatorio_clientes, relatorio_aniversariantes, hub_cashback, relatorio_movimentacoes_cashback, hub_compras, relatorio_pedidos_compra, relatorio_fornecedores, hub_caixa, hub_comissoes, relatorio_comissoes, exportar_comissoes_pdf, exportar_comissoes_xlsx
from financeiro.views import painel_relatorio


app_name = 'relatorios'

urlpatterns = [
    path('comissoes/', hub_comissoes, name='comissoes'),
    path('comissoes/relatorio/', relatorio_comissoes, name='relatorio_comissoes'),
    path('comissoes/relatorio/pdf/', exportar_comissoes_pdf, name='exportar_comissoes_pdf'),
    path('comissoes/relatorio/xlsx/', exportar_comissoes_xlsx, name='exportar_comissoes_xlsx'),
    path('caixa/', hub_caixa, name='caixa'),
    path('compras/', hub_compras, name='compras'),
    path('compras/pedidos/', relatorio_pedidos_compra, name='compras_pedidos'),
    path('compras/fornecedores/', relatorio_fornecedores, name='compras_fornecedores'),
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
