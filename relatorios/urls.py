from django.urls import path

from .views import dashboard


app_name = 'relatorios'

urlpatterns = [
    path('', dashboard, name='dashboard'),
]