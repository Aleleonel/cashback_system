from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse

class F2EA19ContratoComprasFornecedoresTests(SimpleTestCase):
    def test_hub_compras_existe(self):
        self.assertEqual(reverse("relatorios:compras"), "/relatorios/compras/")

    def test_relatorio_pedidos_existe(self):
        self.assertEqual(reverse("relatorios:compras_pedidos"), "/relatorios/compras/pedidos/")

    def test_relatorio_fornecedores_existe(self):
        self.assertEqual(reverse("relatorios:compras_fornecedores"), "/relatorios/compras/fornecedores/")

    def test_sidebar_expoe_compras(self):
        s=Path("templates/partials/sidebar.html").read_text(encoding="utf-8")
        self.assertIn("relatorios:compras",s)

    def test_hub_expoe_dois_relatorios(self):
        s=Path("relatorios/templates/relatorios/compras.html").read_text(encoding="utf-8")
        self.assertIn("relatorios:compras_pedidos",s)
        self.assertIn("relatorios:compras_fornecedores",s)

    def test_views_usam_permissao_relatorios(self):
        s=Path("relatorios/views.py").read_text(encoding="utf-8")
        for nome in ("hub_compras","relatorio_pedidos_compra","relatorio_fornecedores"):
            pos=s.index("def "+nome)
            trecho=s[max(0,pos-250):pos+100]
            self.assertIn("@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)",trecho)

    def test_relatorio_nao_reusa_tela_transacional(self):
        u=Path("relatorios/urls.py").read_text(encoding="utf-8")
        self.assertIn("compras/pedidos/",u)
        self.assertIn("compras/fornecedores/",u)