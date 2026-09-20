from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
PDV = (ROOT / "pdv" / "services" / "vendas" / "caixa.py").read_text(encoding="utf-8")
FIN = (ROOT / "financeiro" / "services.py").read_text(encoding="utf-8")

class IntegracaoCaixaBehaviorRedTests(SimpleTestCase):
    def test_api_pdv_deve_ser_generica_e_nao_importar_financeiro(self):
        inicio = PDV.find("def registrar_movimentacao_caixa_operacional(")
        self.assertNotEqual(inicio, -1)
        bloco = PDV[inicio:inicio+5000]
        self.assertNotIn("from financeiro", bloco)
        self.assertNotIn("BaixaFinanceira", bloco)
        self.assertNotIn("TituloFinanceiro", bloco)

    def test_financeiro_deve_orquestrar_baixa_e_caixa(self):
        self.assertIn("def registrar_baixa_financeira_com_caixa(", FIN)
        self.assertIn("registrar_movimentacao_caixa_operacional", FIN)

    def test_financeiro_deve_orquestrar_estorno_e_caixa(self):
        self.assertIn("def estornar_baixa_financeira_com_caixa(", FIN)
        self.assertIn("movimentacao_estornada", FIN)

    def test_saldo_estorno_de_sangria_deve_ser_positivo(self):
        self.assertIn("movimento.movimentacao_estornada", PDV)
        self.assertIn("TipoMovimentacaoCaixa.SANGRIA", PDV)

    def test_saldo_estorno_de_suprimento_e_venda_deve_ser_negativo(self):
        self.assertIn("TipoMovimentacaoCaixa.SUPRIMENTO", PDV)
        self.assertIn("TipoMovimentacaoCaixa.VENDA", PDV)
        self.assertIn("movimento.movimentacao_estornada", PDV)

    def test_financeiro_nao_deve_criar_movimento_caixa_diretamente(self):
        self.assertNotIn("MovimentacaoCaixa.objects.create(", FIN)