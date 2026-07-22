from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase

from configuracoes.access import (
    validar_acesso_central_configuracoes,
    validar_acesso_configuracoes_criticas,
)


class UsuarioStub:
    is_authenticated = True
    is_superuser = False
    ativo = True
    perfil = "operador"
    matriz = object()


class CentralConfiguracoesAccessTests(SimpleTestCase):
    def test_operador_nao_acessa_central(self):
        usuario = UsuarioStub()

        with self.assertRaises(PermissionDenied):
            validar_acesso_central_configuracoes(usuario=usuario)

    def test_admin_loja_acessa_escopo_empresa(self):
        usuario = UsuarioStub()
        usuario.perfil = "admin_loja"

        contexto = validar_acesso_central_configuracoes(usuario=usuario)

        self.assertEqual(contexto["escopo"], "empresa")
        self.assertFalse(contexto["pode_configuracoes_criticas"])

    def test_superusuario_acessa_configuracoes_criticas(self):
        usuario = UsuarioStub()
        usuario.is_superuser = True

        contexto = validar_acesso_configuracoes_criticas(usuario=usuario)

        self.assertEqual(contexto["escopo"], "plataforma")
        self.assertTrue(contexto["pode_configuracoes_criticas"])

    def test_admin_loja_nao_acessa_configuracoes_criticas(self):
        usuario = UsuarioStub()
        usuario.perfil = "admin_loja"

        with self.assertRaises(PermissionDenied):
            validar_acesso_configuracoes_criticas(usuario=usuario)
