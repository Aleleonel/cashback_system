from pathlib import Path
from django.test import SimpleTestCase

class F2EA19ComportamentoComprasFornecedoresTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views=Path("relatorios/views.py").read_text(encoding="utf-8")
        cls.ped=Path("relatorios/templates/relatorios/compras_pedidos.html").read_text(encoding="utf-8")
        cls.forn=Path("relatorios/templates/relatorios/compras_fornecedores.html").read_text(encoding="utf-8")

    def test_pedidos_tem_periodo_inicial_e_final(self):
        self.assertIn("data_inicio",self.views)
        self.assertIn("data_fim",self.views)
        self.assertIn('name="data_inicio"',self.ped)
        self.assertIn('name="data_fim"',self.ped)

    def test_pedidos_filtram_data_emissao(self):
        self.assertIn("data_emissao__gte",self.views)
        self.assertIn("data_emissao__lte",self.views)

    def test_pedidos_mantem_busca_status(self):
        self.assertIn("get_pedidos_compra",self.views)
        self.assertIn('name="q"',self.ped)
        self.assertIn('name="status"',self.ped)

    def test_fornecedores_mantem_busca_status(self):
        self.assertIn("get_fornecedores",self.views)
        self.assertIn('name="q"',self.forn)
        self.assertIn('name="status"',self.forn)

    def test_paginacao_50(self):
        normal=self.views.replace(" ","")
        self.assertGreaterEqual(normal.count("Paginator("),2)
        self.assertGreaterEqual(normal.count(",50)"),2)

    def test_total_pedidos_usa_total_oficial_modelo(self):
        self.assertIn("x.total",self.views)
        self.assertIn("total_pedidos",self.views)

    def test_sem_acoes_transacionais_nos_relatorios(self):
        conjunto=(self.ped+self.forn).lower()
        for proibido in ("novo fornecedor","novo pedido","editar","excluir","cancelar pedido","receber pedido"):
            self.assertNotIn(proibido,conjunto)