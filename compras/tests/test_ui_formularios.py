from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase


class FormulariosComprasUITests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        base_dir = Path(settings.BASE_DIR)

        cls.fornecedor_path = (
            base_dir
            / "compras"
            / "templates"
            / "compras"
            / "fornecedores"
            / "form.html"
        )

        cls.pedido_path = (
            base_dir
            / "compras"
            / "templates"
            / "compras"
            / "pedidos"
            / "form.html"
        )

    def test_formulario_fornecedor_usa_ui_foundation(self):
        conteudo = self.fornecedor_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "partials/cabecalho_pagina.html",
            conteudo,
        )
        self.assertIn(
            "partials/campo_formulario.html",
            conteudo,
        )
        self.assertIn(
            'class="card shadow-sm border-0"',
            conteudo,
        )
        self.assertIn(
            "Salvar fornecedor",
            conteudo,
        )

    def test_formulario_pedido_usa_ui_foundation(self):
        conteudo = self.pedido_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "partials/cabecalho_pagina.html",
            conteudo,
        )
        self.assertIn(
            "partials/campo_formulario.html",
            conteudo,
        )
        self.assertIn(
            'class="card shadow-sm border-0"',
            conteudo,
        )
        self.assertIn(
            "Salvar pedido",
            conteudo,
        )

    def test_templates_carregam_sem_erro(self):
        get_template(
            "compras/fornecedores/form.html"
        )
        get_template(
            "compras/pedidos/form.html"
        )