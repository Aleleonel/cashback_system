from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


class ViewsProtegidasTest(TestCase):

    def setUp(self):

        self.User = get_user_model()
        
        self.superuser = self.User.objects.create_superuser(
            username='superuser_views',
            password='123456'
        )

        

        self.matriz = Matriz.objects.create(
            nome='Matriz Teste'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Teste',
            status=StatusOperacional.ATIVA,
        )

        self.usuario = self.User.objects.create_user(
            username='usuario_teste',
            password='123456',
            matriz=self.matriz
        )

        self.usuario.perfil = self.User.PERFIL_MASTER
        self.usuario.save()

        self.usuario.lojas.add(self.loja)

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

    def test_dashboard_usuario_autenticado_com_contexto_valido(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('relatorios:dashboard')
        )

        self.assertEqual(response.status_code, 200)

    def test_clientes_usuario_autenticado_com_contexto_valido(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('clientes:lista_clientes')
        )

        self.assertEqual(response.status_code, 200)

    def test_nova_compra_usuario_autenticado_com_contexto_valido(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('cashback:nova_compra')
        )

        self.assertEqual(response.status_code, 200)

    def test_aniversariantes_usuario_autenticado_com_contexto_valido(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('campanhas:aniversariantes_mes')
        )

        self.assertEqual(response.status_code, 200)

    def test_historico_envios_usuario_autenticado_com_contexto_valido(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('campanhas:historico_envios')
        )

        self.assertEqual(response.status_code, 200)

    def test_fila_envios_usuario_autenticado_com_contexto_valido(self):
        self.client.force_login(self.usuario)

        response = self.client.get(
            reverse('campanhas:fila_envios')
        )

        self.assertEqual(response.status_code, 200)

    
    def test_superuser_nao_acessa_dashboard_operacional(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse('relatorios:dashboard')
        )

        self.assertEqual(response.status_code, 403)


    def test_superuser_nao_acessa_clientes_operacional(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse('clientes:lista_clientes')
        )

        self.assertEqual(response.status_code, 403)


    def test_superuser_nao_acessa_nova_compra_operacional(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse('cashback:nova_compra')
        )

        self.assertEqual(response.status_code, 403)


    def test_superuser_nao_acessa_aniversariantes_operacional(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse('campanhas:aniversariantes_mes')
        )

        self.assertEqual(response.status_code, 403)