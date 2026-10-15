from pathlib import Path
from django.test import SimpleTestCase

class F2EA19HardeningUiDatasTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("relatorios/views.py").read_text(encoding="utf-8")
        cls.sidebar = Path("templates/partials/sidebar.html").read_text(encoding="utf-8")

    def test_compras_tem_active_proprio(self):
        self.assertIn("url_name == 'compras'", self.sidebar)
        self.assertIn("url_name == 'compras_pedidos'", self.sidebar)
        self.assertIn("url_name == 'compras_fornecedores'", self.sidebar)

    def test_cadastros_nao_e_fallback_de_todo_relatorios(self):
        self.assertIn("url_name == 'cadastros'", self.sidebar)
        self.assertNotIn("url_name != 'cashback_movimentacoes'", self.sidebar)

    def test_datas_sao_validadas_antes_do_filtro_orm(self):
        self.assertIn("date.fromisoformat(data_inicio)", self.views)
        self.assertIn("date.fromisoformat(data_fim)", self.views)
        self.assertIn("except ValueError", self.views)
        self.assertIn("data_emissao__gte=di", self.views)
        self.assertIn("data_emissao__lte=df", self.views)