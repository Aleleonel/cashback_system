from django.contrib.auth.views import LoginView
from django.urls import reverse


class CashbackLoginView(LoginView):

    template_name = 'registration/login.html'

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse('plataforma:painel_master')

        return reverse('relatorios:dashboard')