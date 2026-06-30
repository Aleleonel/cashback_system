from django.urls import path

from .views import (
    auditoria_empresa,
    dashboard_empresa,
)


app_name = 'empresa'


urlpatterns = [
    path(
        '',
        dashboard_empresa,
        name='dashboard'
    ),

    path(
        'auditoria/',
        auditoria_empresa,
        name='auditoria'
    ),
]