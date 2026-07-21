from django.test import SimpleTestCase
from django.urls import resolve, reverse

from rh.views import inicio


class RhUrlsTests(SimpleTestCase):
    def test_rota_inicial_resolve_view_correta(self):
        match = resolve("/rh/")

        self.assertEqual(match.func, inicio)
        self.assertEqual(match.namespace, "rh")
        self.assertEqual(match.url_name, "inicio")

    def test_rota_inicial_exige_autenticacao(self):
        response = self.client.get(reverse("rh:inicio"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
