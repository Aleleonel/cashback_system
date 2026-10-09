from pathlib import Path
from django.test import SimpleTestCase
from django.urls import reverse


class HubVendasContratoTests(SimpleTestCase):
    def test_rota_hub_vendas(self):
        self.assertEqual(reverse('relatorios:vendas'), '/relatorios/vendas/')

    def test_hub_reusa_historico_pdv(self):
        template = Path('relatorios/templates/relatorios/vendas.html').read_text(encoding='utf-8')
        self.assertIn("{% url 'pdv:historico_vendas' %}", template)
        self.assertIn('Relat\u00f3rio de Vendas', template)

    def test_sidebar_expoe_categorias_cadastros_e_vendas(self):
        sidebar = Path('templates/partials/sidebar.html').read_text(encoding='utf-8')
        self.assertIn("{% url 'relatorios:cadastros' %}", sidebar)
        self.assertIn("{% url 'relatorios:vendas' %}", sidebar)

    def test_hub_nao_inventa_outros_relatorios(self):
        template = Path('relatorios/templates/relatorios/vendas.html').read_text(encoding='utf-8')
        self.assertEqual(template.count("pdv:historico_vendas"), 1)
