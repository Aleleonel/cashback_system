from django.template.loader import get_template
from django.test import SimpleTestCase

from estoque import urls
from estoque.views.dashboard import dashboard_estoque


class DashboardEstoqueUITestCase(SimpleTestCase):
    def test_url_dashboard_estoque_esta_registrada(self):
        padrao = next(
            item
            for item in urls.urlpatterns
            if item.name == 'dashboard_estoque'
        )

        self.assertEqual(
            str(padrao.pattern),
            'dashboard/',
        )
        self.assertIs(
            padrao.callback,
            dashboard_estoque,
        )

    def test_template_dashboard_estoque_carrega(self):
        template = get_template(
            'estoque/dashboard.html'
        )

        self.assertIsNotNone(template)