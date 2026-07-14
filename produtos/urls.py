from django.urls import path

from .views import (
    baixar_modelo_importacao_produtos,
    confirmar_importacao_produtos,
    criar_categoria_view,
    criar_marca_view,
    criar_produto_view,
    criar_unidade_medida_view,
    detalhe_produto,
    editar_categoria_view,
    editar_marca_view,
    editar_produto_view,
    editar_unidade_medida_view,
    importar_produtos_view,
    lista_categorias,
    lista_marcas,
    lista_produtos,
    lista_unidades_medida,
)


app_name = 'produtos'


urlpatterns = [
    path(
        '',
        lista_produtos,
        name='lista_produtos'
    ),
    path(
        'novo/',
        criar_produto_view,
        name='criar_produto'
    ),
    path(
        'importar/',
        importar_produtos_view,
        name='importar_produtos'
    ),
    path(
        'importar/modelo/',
        baixar_modelo_importacao_produtos,
        name='baixar_modelo_importacao'
    ),
    path(
        'importar/confirmar/',
        confirmar_importacao_produtos,
        name='confirmar_importacao'
    ),
    path(
        '<int:produto_id>/',
        detalhe_produto,
        name='detalhe_produto'
    ),
    path(
        '<int:produto_id>/editar/',
        editar_produto_view,
        name='editar_produto'
    ),

    path(
        'categorias/',
        lista_categorias,
        name='lista_categorias'
    ),
    path(
        'categorias/nova/',
        criar_categoria_view,
        name='criar_categoria'
    ),
    path(
        'categorias/<int:categoria_id>/editar/',
        editar_categoria_view,
        name='editar_categoria'
    ),

    path(
        'marcas/',
        lista_marcas,
        name='lista_marcas'
    ),
    path(
        'marcas/nova/',
        criar_marca_view,
        name='criar_marca'
    ),
    path(
        'marcas/<int:marca_id>/editar/',
        editar_marca_view,
        name='editar_marca'
    ),

    path(
        'unidades/',
        lista_unidades_medida,
        name='lista_unidades_medida'
    ),
    path(
        'unidades/nova/',
        criar_unidade_medida_view,
        name='criar_unidade_medida'
    ),
    path(
        'unidades/<int:unidade_id>/editar/',
        editar_unidade_medida_view,
        name='editar_unidade_medida'
    ),
]
