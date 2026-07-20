from django.urls import path

from .views.dashboard import dashboard_estoque
from .views import (
    criar_ajuste_estoque,
    criar_entrada_estoque,
    criar_saida_estoque,
    criar_transferencia_estoque,
    lista_movimentacoes,
)


app_name = 'estoque'


urlpatterns = [
    path(
        'dashboard/',
        dashboard_estoque,
        name='dashboard_estoque',
    ),
    path(
        'entradas/nova/',
        criar_entrada_estoque,
        name='criar_entrada_estoque',
    ),
    path(
        'saidas/nova/',
        criar_saida_estoque,
        name='criar_saida_estoque',
    ),
    path(
        'transferencias/nova/',
        criar_transferencia_estoque,
        name='criar_transferencia_estoque',
    ),
    path(
        'ajustes/novo/',
        criar_ajuste_estoque,
        name='criar_ajuste_estoque',
    ),
    path(
        '',
        lista_movimentacoes,
        name='lista_movimentacoes',
    ),
]