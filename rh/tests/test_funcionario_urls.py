from django.test import SimpleTestCase
from django.urls import resolve, reverse

from rh.views.funcionario_views import (
    funcionario_create,
    funcionario_delete,
    funcionario_list,
    funcionario_update,
)


class FuncionarioUrlsTests(SimpleTestCase):
    def test_rota_lista_resolve_view_correta(self):
        match = resolve("/rh/funcionarios/")

        self.assertEqual(match.func, funcionario_list)
        self.assertEqual(match.namespace, "rh")
        self.assertEqual(match.url_name, "funcionario_list")

    def test_rota_criacao_resolve_view_correta(self):
        match = resolve("/rh/funcionarios/novo/")

        self.assertEqual(match.func, funcionario_create)
        self.assertEqual(match.url_name, "funcionario_create")

    def test_rota_edicao_resolve_view_correta(self):
        match = resolve("/rh/funcionarios/1/editar/")

        self.assertEqual(match.func, funcionario_update)
        self.assertEqual(match.url_name, "funcionario_update")

    def test_rota_inativacao_resolve_view_correta(self):
        match = resolve("/rh/funcionarios/1/inativar/")

        self.assertEqual(match.func, funcionario_delete)
        self.assertEqual(match.url_name, "funcionario_delete")

    def test_lista_exige_autenticacao(self):
        response = self.client.get(
            reverse("rh:funcionario_list")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_criacao_exige_autenticacao(self):
        response = self.client.get(
            reverse("rh:funcionario_create")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)