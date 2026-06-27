from django.urls import path

from .views import lista_auditoria


app_name = 'auditoria'


urlpatterns = [
    path(
        'auditoria/',
        lista_auditoria,
        name='lista_auditoria'
    ),
]