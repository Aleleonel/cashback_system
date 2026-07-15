from django.template.loader import get_template
from django.test import SimpleTestCase


class ProdutosTemplatesTestCase(SimpleTestCase):
    templates = [
        'partials/cabecalho_pagina.html',
        'partials/campo_formulario.html',
        'partials/estado_vazio.html',
        'partials/paginacao.html',
        'produtos/base_catalogo.html',
        'produtos/categorias/lista.html',
        'produtos/categorias/form.html',
        'produtos/marcas/lista.html',
        'produtos/marcas/form.html',
        'produtos/unidades_medida/lista.html',
        'produtos/unidades_medida/form.html',
        'produtos/produtos/lista.html',
        'produtos/produtos/form.html',
        'produtos/produtos/detalhe.html',
    ]

    def test_templates_carregam_sem_erros(self):
        for nome_template in self.templates:
            with self.subTest(
                template=nome_template
            ):
                template = get_template(
                    nome_template
                )

                self.assertIsNotNone(template)
