from django.test import SimpleTestCase
from django.urls import resolve, reverse

from pdv import views


class PdvFoundationTests(SimpleTestCase):
    def test_url_inicio_resolve_view_correta(self):
        url = reverse("pdv:inicio")
        resolver = resolve(url)

        self.assertEqual(url, "/pdv/")
        self.assertEqual(resolver.func, views.inicio)
