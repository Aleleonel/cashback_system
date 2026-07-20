from django.urls import path

from .views import (
    criar_entrada_estoque,
    lista_movimentacoes,
)


app_name = 'estoque'


urlpatterns = [
    path(
        'entradas/nova/',
        criar_entrada_estoque,
        name='criar_entrada_estoque'
    ),
    path(
        '',
        lista_movimentacoes,
        name='lista_movimentacoes'
    ),
]