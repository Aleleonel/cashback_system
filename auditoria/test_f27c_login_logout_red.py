from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.test import RequestFactory, TestCase

from auditoria.models import RegistroAuditoria


class AuditoriaLoginLogoutRedTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="f27c_login_logout",
            password="Teste123!"
        )
        self.rf = RequestFactory()

    def _request(self):
        request = self.rf.get("/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        return request

    def test_signal_login_gera_registro_auditoria(self):
        user_logged_in.send(
            sender=self.User,
            request=self._request(),
            user=self.user,
        )
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=self.user,
                acao=RegistroAuditoria.ACAO_LOGIN,
            ).exists()
        )

    def test_signal_logout_gera_registro_auditoria(self):
        user_logged_out.send(
            sender=self.User,
            request=self._request(),
            user=self.user,
        )
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                usuario=self.user,
                acao=RegistroAuditoria.ACAO_LOGOUT,
            ).exists()
        )