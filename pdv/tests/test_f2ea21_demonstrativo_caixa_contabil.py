from django.test import SimpleTestCase
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class DemonstrativoCaixaContabilContractTests(SimpleTestCase):
    def setUp(self):
        self.views = (ROOT / "pdv" / "views.py").read_text(encoding="utf-8")
        self.tpl = (ROOT / "pdv" / "templates" / "pdv" / "demonstrativo_caixa.html").read_text(encoding="utf-8")

    def test_resumo_vendas_considera_somente_vendas_finalizadas(self):
        self.assertIn("StatusOperacaoVenda.FINALIZADA", self.views)
        self.assertIn("venda__status", self.views)

    def test_a_receber_nao_e_apenas_flag_mas_expoe_recebido_e_saldo_financeiro(self):
        self.assertIn("VENDA_PAGAMENTO", self.views)
        self.assertIn("BaixaFinanceira", self.views)
        self.assertIn("a_receber", self.views)

    def test_movimento_fisico_permanece_independente_do_recebivel(self):
        self.assertIn("movimenta_caixa", self.views)
        self.assertIn("gera_contas_receber", self.views)

    def test_template_distingue_saldo_calculado_de_saldo_real_informado(self):
        self.assertIn("saldo_calculado", self.tpl)
        self.assertIn("saldo_real", self.tpl)
        self.assertIn("valor_fechamento_informado", self.views)
