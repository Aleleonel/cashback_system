from django.urls import path

from .views import (
    aniversariantes_mes,
    disparar_aniversariantes,
    reenviar_aniversariante,
    historico_envios,
    fila_envios,
    configurar_campanha_aniversario,

    lista_templates_campanhas,
    criar_template_campanha,
    editar_template_campanha,
    detalhe_template_campanha_json,
)


app_name = 'campanhas'

urlpatterns = [
    path(
        'aniversariantes/',
        aniversariantes_mes,
        name='aniversariantes_mes'
    ),

    path(
        'aniversariantes/disparar/',
        disparar_aniversariantes,
        name='disparar_aniversariantes'
    ),

    path(
        'aniversariantes/<int:cliente_id>/reenviar/',
        reenviar_aniversariante,
        name='reenviar_aniversariante'
    ),

    path(
        'historico/',
        historico_envios,
        name='historico_envios'
    ),

    path(
        'fila/',
        fila_envios,
        name='fila_envios'
    ),
    
    path(
        'aniversariantes/configuracao/',
        configurar_campanha_aniversario,
        name='configurar_campanha_aniversario'
    ),

    path(
        'templates/',
        lista_templates_campanhas,
        name='lista_templates_campanhas'
    ),

    path(
        'templates/novo/',
        criar_template_campanha,
        name='criar_template_campanha'
    ),

    path(
        'templates/<int:template_id>/editar/',
        editar_template_campanha,
        name='editar_template_campanha'
    ),

    path(
        'templates/<int:template_id>/json/',
        detalhe_template_campanha_json,
        name='detalhe_template_campanha_json'
    ),

    
]