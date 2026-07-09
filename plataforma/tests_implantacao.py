from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from auditoria.models import RegistroAuditoria
from core.choices import StatusOperacional
from core.models import ConfiguracaoSistema
from empresas.models import Loja, Matriz
from plataforma.services import implantar_empresa


class ImplantarEmpresaTest(TestCase):

    def setUp(self):
        self.User = get_user_model()

        self.superuser = self.User.objects.create_superuser(
            username='superuser_implantacao',
            password='123456'
        )

    def test_implantar_empresa_cria_matriz_loja_admin_configuracao_e_auditoria(self):
        request = RequestFactory().post(
            '/painel-master/nova-empresa/',
            REMOTE_ADDR='127.0.0.1',
            HTTP_USER_AGENT='Teste'
        )

        resultado = implantar_empresa(
            dados_matriz={
                'nome': 'Empresa Teste',
                'cnpj': '12345678000199',
            },
            dados_loja={
                'nome': 'Loja Principal',
                'cnpj': '12345678000199',
                'telefone': '11999999999',
            },
            dados_admin={
                'username': 'admin_empresa',
                'email': 'admin@empresa.com',
                'password': 'SenhaForte123',
                'first_name': 'Admin',
            },
            usuario_executor=self.superuser,
            request=request
        )

        matriz = resultado['matriz']
        loja = resultado['loja']
        usuario_admin = resultado['usuario_admin']

        self.assertEqual(Matriz.objects.count(), 1)
        self.assertEqual(Loja.objects.count(), 1)

        self.assertEqual(
            matriz.status,
            StatusOperacional.ATIVA
        )

        self.assertEqual(
            loja.status,
            StatusOperacional.ATIVA
        )

        self.assertEqual(
            usuario_admin.matriz,
            matriz
        )

        self.assertTrue(
            usuario_admin.lojas.filter(id=loja.id).exists()
        )

        self.assertEqual(
            usuario_admin.perfil,
            self.User.PERFIL_MASTER
        )

        self.assertTrue(
            ConfiguracaoSistema.objects.filter(
                matriz=matriz
            ).exists()
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(
                matriz=matriz,
                loja=loja,
                recurso='plataforma.implantacao_empresa'
            ).exists()
        )