from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse, resolve

class F2EA18ContratoCashbackTests(SimpleTestCase):
    def test_rota_hub_cashback_existe(self):
        self.assertEqual(reverse("relatorios:cashback"), "/relatorios/cashback/")

    def test_rota_movimentacoes_cashback_existe(self):
        self.assertEqual(reverse("relatorios:cashback_movimentacoes"), "/relatorios/cashback/movimentacoes/")

    def test_view_movimentacoes_existe(self):
        match = resolve("/relatorios/cashback/movimentacoes/")
        self.assertEqual(match.func.__name__, "relatorio_movimentacoes_cashback")

    def test_selector_global_existe(self):
        from cashback.selectors import get_relatorio_movimentacoes_cashback
        self.assertTrue(callable(get_relatorio_movimentacoes_cashback))

    def test_template_hub_existe(self):
        self.assertTrue(Path("relatorios/templates/relatorios/cashback.html").exists())

    def test_template_movimentacoes_existe(self):
        self.assertTrue(Path("relatorios/templates/relatorios/cashback_movimentacoes.html").exists())

    def test_sidebar_expoe_relatorio_cashback(self):
        texto=Path("templates/partials/sidebar.html").read_text(encoding="utf-8")
        self.assertIn("relatorios:cashback", texto)
        self.assertIn("Cashback", texto)

    def test_view_usa_permissao_relatorios(self):
        texto=Path("relatorios/views.py").read_text(encoding="utf-8")
        self.assertIn("def relatorio_movimentacoes_cashback", texto)
        trecho=texto.split("def relatorio_movimentacoes_cashback",1)[0][-500:]
        self.assertIn("PERMISSAO_RELATORIOS_DASHBOARD", trecho)
