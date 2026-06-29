from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from core.choices import StatusOperacional
from core.services import get_contexto_operacional_usuario
from empresas.models import Loja, Matriz

from core.services import get_contexto_plataforma

class ContextoOperacionalUsuarioTest(TestCase):

    def setUp(self):
        self.User = get_user_model()

        self.matriz = Matriz.objects.create(
            nome='Matriz Teste'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Teste',
            status=StatusOperacional.ATIVA,
        )

    def test_usuario_nao_autenticado_gera_permission_denied(self):

        class UsuarioAnonimo:
            is_authenticated = False

        with self.assertRaises(PermissionDenied):
            get_contexto_operacional_usuario(
                UsuarioAnonimo()
            )

    def test_usuario_sem_matriz_gera_validation_error(self):
        usuario = self.User.objects.create_user(
            username='sem_matriz',
            password='123456'
        )

        with self.assertRaises(ValidationError):
            get_contexto_operacional_usuario(usuario)

    def test_usuario_sem_loja_ativa_gera_validation_error(self):
        usuario = self.User.objects.create_user(
            username='sem_loja',
            password='123456',
            matriz=self.matriz
        )

        with self.assertRaises(ValidationError):
            get_contexto_operacional_usuario(usuario)

    def test_usuario_com_matriz_e_loja_ativa_retorna_contexto(self):
        usuario = self.User.objects.create_user(
            username='usuario_ok',
            password='123456',
            matriz=self.matriz
        )

        usuario.lojas.add(self.loja)

        contexto = get_contexto_operacional_usuario(usuario)

        self.assertEqual(
            contexto['matriz'],
            self.matriz
        )

        self.assertEqual(
            contexto['loja'],
            self.loja
        )
        

class ContextoPlataformaTest(TestCase):

    def setUp(self):
        self.User = get_user_model()

    def test_usuario_nao_autenticado_nao_acessa_contexto_plataforma(self):

        class UsuarioAnonimo:
            is_authenticated = False
            is_superuser = False

        with self.assertRaises(PermissionDenied):
            get_contexto_plataforma(
                UsuarioAnonimo()
            )

    def test_usuario_comum_nao_acessa_contexto_plataforma(self):
        usuario = self.User.objects.create_user(
            username='usuario_comum',
            password='123456'
        )

        with self.assertRaises(PermissionDenied):
            get_contexto_plataforma(usuario)

    def test_superuser_acessa_contexto_plataforma(self):
        usuario = self.User.objects.create_superuser(
            username='superuser_contexto',
            password='123456'
        )

        contexto = get_contexto_plataforma(usuario)

        self.assertEqual(
            contexto['usuario'],
            usuario
        )