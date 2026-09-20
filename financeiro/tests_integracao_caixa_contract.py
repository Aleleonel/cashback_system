from pathlib import Path

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parent.parent
PDV_CAIXA = ROOT / "pdv" / "services" / "vendas" / "caixa.py"
FIN_SERVICES = ROOT / "financeiro" / "services.py"


class IntegracaoCaixaFinanceiroContractRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pdv_text = PDV_CAIXA.read_text(encoding="utf-8")
        cls.fin_text = FIN_SERVICES.read_text(encoding="utf-8")

    def test_pdv_deve_expor_servico_generico_de_movimento_operacional(self):
        self.assertIn("def registrar_movimentacao_caixa_operacional(", self.pdv_text)

    def test_servico_generico_deve_validar_sessao_aberta(self):
        self.assertIn("StatusSessaoCaixa.ABERTA", self.pdv_text)
        self.assertIn("registrar_movimentacao_caixa_operacional", self.pdv_text)

    def test_servico_generico_deve_suportar_suprimento_e_sangria(self):
        self.assertIn("TipoMovimentacaoCaixa.SUPRIMENTO", self.pdv_text)
        self.assertIn("TipoMovimentacaoCaixa.SANGRIA", self.pdv_text)
        self.assertIn("registrar_movimentacao_caixa_operacional", self.pdv_text)

    def test_financeiro_deve_expor_baixa_com_integracao_caixa(self):
        self.assertIn("def registrar_baixa_financeira_com_caixa(", self.fin_text)

    def test_baixa_com_caixa_deve_reutilizar_registrar_baixa_financeira(self):
        self.assertIn("registrar_baixa_financeira(", self.fin_text)
        self.assertIn("registrar_baixa_financeira_com_caixa", self.fin_text)

    def test_baixa_com_caixa_deve_reutilizar_servico_pdv_generico(self):
        self.assertIn("registrar_movimentacao_caixa_operacional", self.fin_text)

    def test_pagar_deve_mapear_para_sangria_e_receber_para_suprimento(self):
        self.assertIn("TipoMovimentacaoCaixa.SANGRIA", self.fin_text)
        self.assertIn("TipoMovimentacaoCaixa.SUPRIMENTO", self.fin_text)

    def test_financeiro_nao_deve_criar_movimentacao_caixa_diretamente(self):
        bloco = self.fin_text
        self.assertNotIn("MovimentacaoCaixa.objects.create(", bloco)

    def test_integracao_deve_ser_atomica(self):
        marcador = "def registrar_baixa_financeira_com_caixa("
        indice = self.fin_text.find(marcador)
        self.assertNotEqual(indice, -1)
        prefixo = self.fin_text[max(0, indice - 100):indice]
        self.assertIn("@transaction.atomic", prefixo)

    def test_estorno_financeiro_com_caixa_deve_ser_rastreavel(self):
        self.assertIn("def estornar_baixa_financeira_com_caixa(", self.fin_text)
        self.assertIn("movimentacao_estornada", self.pdv_text)
        self.assertIn("TipoMovimentacaoCaixa.ESTORNO", self.pdv_text)