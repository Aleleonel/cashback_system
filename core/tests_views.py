from django.test import TestCase
from django.urls import reverse


class ViewsProtegidasTest(TestCase):

    def test_dashboard_exige_login(self):
        response = self.client.get(
            reverse('relatorios:dashboard')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_clientes_exige_login(self):
        response = self.client.get(
            reverse('clientes:lista_clientes')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_nova_compra_exige_login(self):
        response = self.client.get(
            reverse('cashback:nova_compra')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_aniversariantes_exige_login(self):
        response = self.client.get(
            reverse('campanhas:aniversariantes_mes')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_historico_envios_exige_login(self):
        response = self.client.get(
            reverse('campanhas:historico_envios')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_fila_envios_exige_login(self):
        response = self.client.get(
            reverse('campanhas:fila_envios')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)