from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from empresas.models import Loja, Matriz


class PainelMasterTest(TestCase):

    def setUp(self):
        self.User = get_user_model()

        self.matriz = Matriz.objects.create(
            nome='Matriz Teste'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Teste',
            ativa=True
        )

        self.usuario_matriz = self.User.objects.create_user(
            username='admin_matriz',
            password='123456',
            matriz=self.matriz,
            perfil='master'
        )

        self.usuario_matriz.lojas.add(self.loja)

        self.superuser = self.User.objects.create_superuser(
            username='superuser',
            password='123456'
        )

    def test_painel_master_exige_login(self):
        response = self.client.get(
            reverse('plataforma:painel_master')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_usuario_matriz_nao_acessa_painel_master(self):
        self.client.force_login(self.usuario_matriz)

        response = self.client.get(
            reverse('plataforma:painel_master')
        )

        self.assertEqual(
            response.status_code,
            403
        )

    def test_superuser_acessa_painel_master(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse('plataforma:painel_master')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Painel Master'
        )