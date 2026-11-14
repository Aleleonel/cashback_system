"""F32-RET48: isolated ACL grant/revoke and matrix/store scope regression."""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import PermissaoUsuario
from accounts.services import usuario_tem_permissao
from empresa.services import sincronizar_permissoes_extras_usuario_empresa
from empresas.models import Matriz, Loja
from pdv.models import Caixa, SessaoCaixa
from pdv.constants import (PERMISSAO_PDV_FECHAR_CAIXA, PERMISSAO_PDV_SANGRIA,
    PERMISSAO_PDV_SUPRIMENTO, PERMISSAO_PDV_CANCELAR_VENDA,
    PERMISSAO_PDV_VISUALIZAR, PERMISSAO_PDV_OPERAR, PERMISSAO_PDV_ABRIR_CAIXA)

class F32RET48ACLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.ma = Matriz.objects.create(nome='RET48 Matriz A')
        cls.mb = Matriz.objects.create(nome='RET48 Matriz B')
        cls.a1 = Loja.objects.create(matriz=cls.ma, nome='RET48 A1')
        cls.a2 = Loja.objects.create(matriz=cls.ma, nome='RET48 A2')
        cls.b1 = Loja.objects.create(matriz=cls.mb, nome='RET48 B1')
        cls.op = User.objects.create_user(username='ret48_operator', password='test_only',
            perfil=User.PERFIL_OPERADOR, matriz=cls.ma, ativo=True)
        cls.op.lojas.set([cls.a1])
        cls.other = User.objects.create_user(username='ret48_other', password='test_only',
            perfil=User.PERFIL_OPERADOR, matriz=cls.mb, ativo=True)
        cls.other.lojas.set([cls.b1])
        cls.ca = Caixa.objects.create(matriz=cls.ma, loja=cls.a1, nome='RET48 caixa A', codigo='RET48A')
        cls.cb = Caixa.objects.create(matriz=cls.mb, loja=cls.b1, nome='RET48 caixa B', codigo='RET48B')
        cls.sa = SessaoCaixa.objects.create(caixa=cls.ca, operador_abertura=cls.op)
        cls.sb = SessaoCaixa.objects.create(caixa=cls.cb, operador_abertura=cls.other)

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.client.force_login(self.op)

    def test_basic_permissions_remain_inherited(self):
        for permission in (PERMISSAO_PDV_VISUALIZAR, PERMISSAO_PDV_OPERAR, PERMISSAO_PDV_ABRIR_CAIXA):
            with self.subTest(permission=permission):
                self.assertTrue(usuario_tem_permissao(self.op, permission))

    def test_grant_revoke_privileged_permissions(self):
        privileged = (PERMISSAO_PDV_FECHAR_CAIXA, PERMISSAO_PDV_SANGRIA,
            PERMISSAO_PDV_SUPRIMENTO, PERMISSAO_PDV_CANCELAR_VENDA)
        for permission in privileged:
            with self.subTest(permission=permission):
                self.assertFalse(usuario_tem_permissao(self.op, permission))
                PermissaoUsuario.objects.create(usuario=self.op, permissao=permission)
                self.assertTrue(usuario_tem_permissao(self.op, permission))
                self.op.permissoes_extras.filter(permissao=permission).delete()
                self.assertFalse(usuario_tem_permissao(self.op, permission))

    def test_http_history_grant_and_revoke(self):
        url = reverse('pdv:historico_fechamentos')
        self.assertEqual(self.client.get(url).status_code, 403)
        grant = PermissaoUsuario.objects.create(usuario=self.op, permissao=PERMISSAO_PDV_FECHAR_CAIXA)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.sa.pk, {s.pk for s in response.context['sessoes']})
        self.assertNotIn(self.sb.pk, {s.pk for s in response.context['sessoes']})
        grant.delete()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_cannot_select_store_outside_assigned_scope(self):
        url = reverse('pdv:selecionar_loja_operacional')
        for target in (self.a2, self.b1):
            with self.subTest(store=target.pk):
                response = self.client.post(url, {'loja_operacional_id': str(target.pk)})
                self.assertNotEqual(response.status_code, 500)
                self.assertNotEqual(self.client.session.get('loja_operacional_id'), target.pk)

    def test_cross_matrix_demonstrative_is_404(self):
        PermissaoUsuario.objects.create(usuario=self.op, permissao=PERMISSAO_PDV_FECHAR_CAIXA)
        url = reverse('pdv:demonstrativo_caixa', kwargs={'sessao_id': self.sb.pk})
        self.assertEqual(self.client.get(url).status_code, 404)