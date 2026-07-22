from django.test import SimpleTestCase
from django.urls import resolve, reverse

from configuracoes import views


class ConfiguracoesUrlsTests(SimpleTestCase):
    def test_url_inicio(self):
        url = reverse("configuracoes:inicio")
        self.assertEqual(resolve(url).func, views.inicio)

    def test_url_criticas(self):
        url = reverse("configuracoes:criticas")
        self.assertEqual(resolve(url).func, views.criticas)
