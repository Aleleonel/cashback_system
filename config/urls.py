from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


urlpatterns = [
    path('', lambda request: redirect('cashback:nova_compra')),
    path('admin/', admin.site.urls),
    path('cashback/', include('cashback.urls')),
    path('clientes/', include('clientes.urls')),
    path('dashboard/', include('relatorios.urls')),
    path('campanhas/', include('campanhas.urls')),
]