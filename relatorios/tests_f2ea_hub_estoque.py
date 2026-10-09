from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse

class HubEstoqueContratoTests(SimpleTestCase):
    def test_rota_hub_estoque(self):
        self.assertEqual(reverse('relatorios:estoque'), '/relatorios/estoque/')

    def test_hub_reusa_lista_movimentacoes(self):
        template = Path('relatorios/templates/relatorios/estoque.html').read_text(encoding='utf-8')
        self.assertIn("{% url 'estoque:lista_movimentacoes' %}", template)
        self.assertIn('Relatório de Movimentações de Estoque', template)

    def test_sidebar_expoe_tres_categorias(self):
        sidebar = Path('templates/partials/sidebar.html').read_text(encoding='utf-8')
        self.assertIn("{% url 'relatorios:cadastros' %}", sidebar)
        self.assertIn("{% url 'relatorios:vendas' %}", sidebar)
        self.assertIn("{% url 'relatorios:estoque' %}", sidebar)

    def test_hub_nao_inventa_outros_relatorios(self):
        template = Path('relatorios/templates/relatorios/estoque.html').read_text(encoding='utf-8')
        self.assertEqual(template.count("estoque:lista_movimentacoes"), 1)
