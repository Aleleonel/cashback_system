from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'perfil',
        'matriz',
        'ativo',
        'is_staff',
    )

    list_filter = (
        'perfil',
        'ativo',
        'is_staff',
        'is_superuser',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Dados do Sistema', {
            'fields': (
                'perfil',
                'matriz',
                'lojas',
                'telefone',
                'ativo',
            )
        }),
    )

    filter_horizontal = (
        'groups',
        'user_permissions',
        'lojas',
    )