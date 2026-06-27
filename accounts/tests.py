from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.services import (
    PERMISSAO_CAMPANHAS_CONFIGURAR,
    PERMISSAO_CAMPANHAS_DISPARAR,
    PERMISSAO_CLIENTES_IMPORTAR,
    PERMISSAO_DASHBOARD,
    usuario_tem_permissao,
    exigir_permissao,
)
from empresas.models import Matriz


class PermissoesUsuarioTest(TestCase):

    def setUp(self):
        self.User = get_user_model()

        self.matriz = Matriz.objects.create(
            nome='Matriz Teste'
        )

    def criar_usuario(self, perfil, ativo=True):
        return self.User.objects.create_user(
            username=f'usuario_{perfil}_{ativo}',
            password='123456',
            matriz=self.matriz,
            perfil=perfil,
            ativo=ativo
        )

    def test_master_tem_permissao_total(self):
        usuario = self.criar_usuario('master')

        self.assertTrue(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_CAMPANHAS_CONFIGURAR
            )
        )

        self.assertTrue(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_CLIENTES_IMPORTAR
            )
        )

    def test_admin_loja_nao_configura_campanha(self):
        usuario = self.criar_usuario('admin_loja')

        self.assertFalse(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_CAMPANHAS_CONFIGURAR
            )
        )

    def test_admin_loja_pode_disparar_campanha(self):
        usuario = self.criar_usuario('admin_loja')

        self.assertTrue(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_CAMPANHAS_DISPARAR
            )
        )

    def test_operador_nao_importa_clientes(self):
        usuario = self.criar_usuario('operador')

        self.assertFalse(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_CLIENTES_IMPORTAR
            )
        )

    def test_usuario_inativo_nao_tem_permissao(self):
        usuario = self.criar_usuario(
            'master',
            ativo=False
        )

        self.assertFalse(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_DASHBOARD
            )
        )

    def test_exigir_permissao_lanca_permission_denied(self):
        usuario = self.criar_usuario('operador')

        with self.assertRaises(PermissionDenied):
            exigir_permissao(
                usuario,
                PERMISSAO_CAMPANHAS_CONFIGURAR
            )