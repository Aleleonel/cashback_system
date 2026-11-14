"""F32-RET38: privileged PDV HTTP denials, test database only."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class PrivilegedPdvHttpDenialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.operator = User.objects.create_user(
            username="f32_ret38_operator", password="test_only_password",
            perfil=User.PERFIL_OPERADOR, ativo=True,
        )

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.client.force_login(self.operator)

    def test_operator_has_basic_pdv_permission(self):
        from accounts.services import usuario_tem_permissao
        from pdv.constants import (
            PERMISSAO_PDV_VISUALIZAR, PERMISSAO_PDV_OPERAR,
            PERMISSAO_PDV_ABRIR_CAIXA,
        )
        for permission in (PERMISSAO_PDV_VISUALIZAR,
                           PERMISSAO_PDV_OPERAR, PERMISSAO_PDV_ABRIR_CAIXA):
            with self.subTest(permission=permission):
                self.assertTrue(usuario_tem_permissao(self.operator, permission))

    def test_operator_lacks_privileged_permissions(self):
        from accounts.services import usuario_tem_permissao
        from pdv.constants import (
            PERMISSAO_PDV_FECHAR_CAIXA, PERMISSAO_PDV_SANGRIA,
            PERMISSAO_PDV_SUPRIMENTO, PERMISSAO_PDV_CANCELAR_VENDA,
            PERMISSAO_PDV_AUTORIZAR_DESCONTO,
        )
        for permission in (PERMISSAO_PDV_FECHAR_CAIXA,
                           PERMISSAO_PDV_SANGRIA, PERMISSAO_PDV_SUPRIMENTO,
                           PERMISSAO_PDV_CANCELAR_VENDA,
                           PERMISSAO_PDV_AUTORIZAR_DESCONTO):
            with self.subTest(permission=permission):
                self.assertFalse(usuario_tem_permissao(self.operator, permission))

    def test_privileged_http_denied_without_grant(self):
        cases = (
            ("GET", "pdv:fechar_caixa"),
            ("POST", "pdv:confirmar_fechamento_caixa"),
            ("GET", "pdv:suprimento_caixa"),
            ("POST", "pdv:suprimento_caixa"),
            ("GET", "pdv:sangria_caixa"),
            ("POST", "pdv:sangria_caixa"),
            ("POST", "pdv:cancelar_venda"),
            ("GET", "pdv:historico_fechamentos"),
        )
        for method, route in cases:
            with self.subTest(method=method, route=route):
                url = reverse(route)
                response = getattr(self.client, method.lower())(url)
                self.assertEqual(response.status_code, 403,
                                 f"{method} {url}: got {response.status_code}")