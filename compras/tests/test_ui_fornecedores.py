from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class ListaFornecedoresUITests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.lista_path = (
            Path(settings.BASE_DIR)
            / "compras"
            / "templates"
            / "compras"
            / "fornecedores"
            / "lista.html"
        )

        cls.tabela_path = (
            cls.lista_path.parent
            / "_tabela_conteudo.html"
        )

        cls.paginacao_path = (
            Path(settings.BASE_DIR)
            / "templates"
            / "partials"
            / "paginacao.html"
        )

    def test_lista_usa_componentes_ui_foundation(self):
        conteudo = self.lista_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "partials/cabecalho_pagina.html",
            conteudo,
        )
        self.assertIn(
            "partials/toolbar_lista.html",
            conteudo,
        )
        self.assertIn(
            "partials/tabela_base.html",
            conteudo,
        )
        self.assertIn(
            "partials/paginacao.html",
            conteudo,
        )
        self.assertIn(
            "status_opcoes=status_choices",
            conteudo,
        )

    def test_tabela_usa_estado_vazio(self):
        conteudo = self.tabela_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "partials/estado_vazio.html",
            conteudo,
        )
        self.assertIn(
            "compras:editar_fornecedor",
            conteudo,
        )
        self.assertIn(
            "badge text-bg-success",
            conteudo,
        )

    def test_paginacao_preserva_status(self):
        conteudo = self.paginacao_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "&status={{ status|urlencode }}",
            conteudo,
        )