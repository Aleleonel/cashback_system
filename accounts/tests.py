from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from django.test import RequestFactory
from django.http import HttpResponse
from accounts.decorators import require_permission

from accounts.permissions import (
    PERMISSAO_CAMPANHAS_CONFIGURAR,
    PERMISSAO_CAMPANHAS_DISPARAR,
    PERMISSAO_CLIENTES_IMPORTAR,
    PERMISSAO_DASHBOARD,
    PERMISSAO_PLATAFORMA_PAINEL_MASTER,
)

from accounts.services import (
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

    def test_admin_loja_configura_campanha(self):
        usuario = self.User.objects.create_user(
            username='admin_loja_campanha',
            password='123456',
            perfil=self.User.PERFIL_ADMIN_LOJA,
            ativo=True
        )

        self.assertTrue(
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

    def test_superuser_tem_acesso_total(self):
        usuario = self.User.objects.create_superuser(
            username='superuser',
            password='123456'
        )

        self.assertTrue(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_PLATAFORMA_PAINEL_MASTER
            )
        )

        self.assertTrue(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_CAMPANHAS_CONFIGURAR
            )
        )


    def test_usuario_master_da_matriz_nao_acessa_painel_master(self):
        usuario = self.criar_usuario('master')

        self.assertFalse(
            usuario_tem_permissao(
                usuario,
                PERMISSAO_PLATAFORMA_PAINEL_MASTER
            )
        )
    
    def test_decorator_permite_usuario_com_permissao(self):
        usuario = self.criar_usuario('master')

        request = RequestFactory().get('/teste/')
        request.user = usuario

    @require_permission(PERMISSAO_DASHBOARD)
    def view_teste(request):
        return HttpResponse('OK')

        response = view_teste(request)

        self.assertEqual(response.status_code, 200)


    def test_decorator_bloqueia_usuario_sem_permissao(self):
        usuario = self.criar_usuario('operador')

        request = RequestFactory().get('/teste/')
        request.user = usuario

    @require_permission(PERMISSAO_CAMPANHAS_CONFIGURAR)
    def view_teste(request):
        return HttpResponse('OK')

        with self.assertRaises(PermissionDenied):
            view_teste(request)