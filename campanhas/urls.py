from django.urls import path

from .views import aniversariantes_mes


app_name = 'campanhas'

urlpatterns = [
    path(
        'aniversariantes/',
        aniversariantes_mes,
        name='aniversariantes_mes'
    ),
]