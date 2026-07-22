from django.test import SimpleTestCase
from django.urls import resolve, reverse

from rh.views.departamento_views import (
    departamento_create,
    departamento_delete,
    departamento_list,
    departamento_update,
)


class DepartamentoUrlsTests(SimpleTestCase):
    def test_rota_lista_resolve_view_correta(self):
        match = resolve("/rh/departamentos/")

        self.assertEqual(match.func, departamento_list)
        self.assertEqual(match.namespace, "rh")
        self.assertEqual(match.url_name, "departamento_list")

    def test_rota_criacao_resolve_view_correta(self):
        match = resolve("/rh/departamentos/novo/")

        self.assertEqual(match.func, departamento_create)
        self.assertEqual(match.url_name, "departamento_create")

    def test_rota_edicao_resolve_view_correta(self):
        match = resolve("/rh/departamentos/1/editar/")

        self.assertEqual(match.func, departamento_update)
        self.assertEqual(match.url_name, "departamento_update")

    def test_rota_inativacao_resolve_view_correta(self):
        match = resolve("/rh/departamentos/1/inativar/")

        self.assertEqual(match.func, departamento_delete)
        self.assertEqual(match.url_name, "departamento_delete")

    def test_lista_exige_autenticacao(self):
        response = self.client.get(
            reverse("rh:departamento_list")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_criacao_exige_autenticacao(self):
        response = self.client.get(
            reverse("rh:departamento_create")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)