from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from auditoria.models import RegistroAuditoria
from auditoria.services import registrar_auditoria
from empresas.models import Loja, Matriz


class RegistroAuditoriaTest(TestCase):

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

        self.usuario = self.User.objects.create_user(
            username='usuario_teste',
            password='123456',
            matriz=self.matriz
        )

    def test_registra_auditoria_com_usuario_contexto_e_request(self):
        request = RequestFactory().get(
            '/clientes/',
            HTTP_USER_AGENT='Teste Browser',
            REMOTE_ADDR='127.0.0.1'
        )

        registro = registrar_auditoria(
            usuario=self.usuario,
            matriz=self.matriz,
            loja=self.loja,
            acao=RegistroAuditoria.ACAO_ACESSAR,
            recurso='clientes.lista',
            recurso_id=123,
            descricao='Acesso à lista de clientes',
            request=request
        )

        self.assertEqual(registro.usuario, self.usuario)
        self.assertEqual(registro.matriz, self.matriz)
        self.assertEqual(registro.loja, self.loja)
        self.assertEqual(registro.acao, RegistroAuditoria.ACAO_ACESSAR)
        self.assertEqual(registro.recurso, 'clientes.lista')
        self.assertEqual(registro.recurso_id, '123')
        self.assertEqual(registro.ip, '127.0.0.1')
        self.assertEqual(registro.user_agent, 'Teste Browser')