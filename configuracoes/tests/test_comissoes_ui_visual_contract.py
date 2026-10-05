from pathlib import Path
from django.test import SimpleTestCase
class ComissoesVisualContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.html=(Path(__file__).resolve().parents[1]/"templates"/"configuracoes"/"comissoes.html").read_text(encoding="utf-8")
    def test_cabecalho(self):
        self.assertIn("Vendas e comissões",self.html); self.assertIn("Configurações comerciais",self.html); self.assertIn("bi-percent",self.html)
    def test_politica(self):
        self.assertIn("form-check form-switch",self.html); self.assertIn('class="form-label"',self.html); self.assertIn('class="input-group-text">R$</span>',self.html)
    def test_metas(self):
        self.assertGreaterEqual(self.html.count('class="input-group"'),3); self.assertIn('class="input-group-text">%</span>',self.html); self.assertIn('class="table-responsive"',self.html); self.assertIn("Nenhuma meta cadastrada",self.html)
    def test_fechamento(self):
        self.assertIn("Fechamento mensal",self.html); self.assertIn("Fechar comissões",self.html); self.assertIn("Histórico de fechamentos",self.html)
    def test_acoes(self):
        self.assertIn("btn-outline-secondary",self.html); self.assertIn("Salvar política",self.html); self.assertIn("Adicionar meta",self.html)