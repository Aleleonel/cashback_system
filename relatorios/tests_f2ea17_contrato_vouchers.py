from pathlib import Path
from django.test import SimpleTestCase


class F2EA17ContratoVouchersTest(SimpleTestCase):
    def test_rota_hub_vouchers_deve_existir(self):
        urls = Path("relatorios/urls.py").read_text(encoding="utf-8")
        self.assertIn("name='vouchers'", urls)

    def test_rota_relatorio_utilizacoes_deve_existir(self):
        urls = Path("relatorios/urls.py").read_text(encoding="utf-8")
        self.assertIn("name='vouchers_utilizacoes'", urls)

    def test_view_relatorio_utilizacoes_deve_existir(self):
        views = Path("relatorios/views.py").read_text(encoding="utf-8")
        self.assertIn("def relatorio_utilizacao_vouchers(", views)

    def test_selector_relatorio_deve_existir(self):
        selectors = Path("vouchers/selectors.py").read_text(encoding="utf-8")
        self.assertIn("def get_relatorio_usos_voucher(", selectors)

    def test_sidebar_deve_expor_categoria_vouchers_em_relatorios(self):
        sidebar = Path("templates/partials/sidebar.html").read_text(encoding="utf-8")
        self.assertIn("{% url 'relatorios:vouchers' %}", sidebar)

    def test_templates_relatorio_devem_existir(self):
        self.assertTrue(Path("relatorios/templates/relatorios/vouchers.html").exists())
        self.assertTrue(Path("relatorios/templates/relatorios/vouchers_utilizacao.html").exists())
