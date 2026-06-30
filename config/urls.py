from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.contrib.auth.views import LogoutView
from accounts.views import CashbackLoginView


urlpatterns = [
    path('', lambda request: redirect('cashback:nova_compra')),
    path('admin/', admin.site.urls),
    path('cashback/', include('cashback.urls')),
    path('clientes/', include('clientes.urls')),
    path('dashboard/', include('relatorios.urls')),
    path('campanhas/', include('campanhas.urls')),
    
    path(
        'login/',
        CashbackLoginView.as_view(),
        name='login'
    ),

    path(
        'logout/',
        LogoutView.as_view(

        ),
        name='logout'
    ),

    path(
        '',
        include(
        'plataforma.urls'
        )
    ),

    path(
        '',
        include(
        'auditoria.urls'
        )
    ),

    path('', include('accounts.urls')),

    path('empresa/', include('empresa.urls')),
]