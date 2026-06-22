from django.contrib import admin

from .models import Matriz, Loja


@admin.register(Matriz)
class MatrizAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'ativa', 'criada_em')
    search_fields = ('nome', 'cnpj')
    list_filter = ('ativa',)


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matriz', 'cnpj', 'telefone', 'ativa')
    search_fields = ('nome', 'cnpj', 'matriz__nome')
    list_filter = ('ativa', 'matriz')