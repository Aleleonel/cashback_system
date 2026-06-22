from django.urls import path

from . import views


app_name = 'cashback'

urlpatterns = [
    path('nova-compra/', views.nova_compra, name='nova_compra'),
]