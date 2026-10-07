from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from accounts.views.login import CashbackLoginView

class LoginDashboardRegressaoTests(SimpleTestCase):
    def test_dashboard_global_resolve(self):
        self.assertEqual(reverse("dashboard"), "/dashboard/")

    def test_login_usuario_comum_redireciona_dashboard_global(self):
        User = get_user_model()
        usuario = User(is_superuser=False)
        request = RequestFactory().get("/login/")
        request.user = usuario
        view = CashbackLoginView()
        view.request = request
        self.assertEqual(view.get_success_url(), "/dashboard/")
