from django.urls import path

from .views import lista_movimentacoes


app_name = 'estoque'


urlpatterns = [
    path(
        '',
        lista_movimentacoes,
        name='lista_movimentacoes'
    ),
]