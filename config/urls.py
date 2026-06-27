from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('', lambda request: redirect('cashback:nova_compra')),
    path('admin/', admin.site.urls),
    path('cashback/', include('cashback.urls')),
    path('clientes/', include('clientes.urls')),
    path('dashboard/', include('relatorios.urls')),
    path('campanhas/', include('campanhas.urls')),
    
    path(
        'login/',
        LoginView.as_view(
            template_name='registration/login.html'
        ),
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
]