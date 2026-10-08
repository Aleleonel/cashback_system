from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse

class RelatoriosNavegacaoEncodingTests(SimpleTestCase):
    def test_dashboard_permanece_em_dashboard(self):
        self.assertEqual(reverse("dashboard"), "/dashboard/")

    def test_relatorio_clientes_fica_em_relatorios_cadastros(self):
        self.assertEqual(reverse("relatorios:clientes"), "/relatorios/cadastros/clientes/")

    def test_relatorio_aniversariantes_fica_em_relatorios_cadastros(self):
        self.assertEqual(reverse("relatorios:aniversariantes"), "/relatorios/cadastros/aniversariantes/")

    def test_sidebar_tem_secao_relatorios_sem_substituir_clientes_operacional(self):
        root = Path(__file__).resolve().parent.parent
        sidebar = (root / "templates" / "partials" / "sidebar.html").read_text(encoding="utf-8")
        self.assertIn("data-sidebar-section=" + chr(34) + "clientes" + chr(34), sidebar)
        self.assertIn("clientes:lista_clientes", sidebar)
        self.assertIn("data-sidebar-section=" + chr(34) + "relatorios" + chr(34), sidebar)
        self.assertIn("relatorios:cadastros", sidebar)

