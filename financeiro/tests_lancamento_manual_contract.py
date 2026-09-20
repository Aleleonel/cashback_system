from pathlib import Path
from django.test import SimpleTestCase

class LancamentoManualContractRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.services = Path("financeiro/services.py").read_text(encoding="utf-8")

    def test_existe_servico_criar_lancamento_manual(self):
        self.assertIn("def criar_lancamento_manual(", self.services)

    def test_servico_manual_exige_plano_conta(self):
        self.assertIn("plano_conta", self.services)
        self.assertIn("aceita_lancamento", self.services)

    def test_servico_manual_restringe_origem_manual(self):
        self.assertIn("OrigemTipo.MANUAL", self.services)

    def test_servico_manual_valida_escopo_matriz(self):
        self.assertIn("matriz", self.services)
        self.assertIn("centro_custo", self.services)
        self.assertIn("loja", self.services)

    def test_servico_manual_suporta_parcelamento(self):
        self.assertIn("parcelas", self.services)
        self.assertIn("vencimento", self.services)

    def test_servico_manual_e_transacional(self):
        self.assertIn("@transaction.atomic", self.services)

    def test_servico_manual_reusa_criar_titulo_financeiro(self):
        self.assertIn("criar_titulo_financeiro(", self.services)

    def test_servico_manual_nao_movimenta_caixa_neste_bloco(self):
        trecho = self.services[self.services.find("def criar_lancamento_manual("):]
        if trecho:
            trecho = trecho[:6000]
        self.assertNotIn("MovimentacaoCaixa.objects.create", trecho)