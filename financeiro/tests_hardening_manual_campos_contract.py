from pathlib import Path
from django.test import SimpleTestCase

class HardeningManualCamposContractRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.models = Path("financeiro/models.py").read_text(encoding="utf-8")
        cls.services = Path("financeiro/services.py").read_text(encoding="utf-8")

    def test_titulo_deve_persistir_data_competencia(self):
        self.assertIn("data_competencia = models.DateField", self.models)

    def test_titulo_deve_persistir_valor_bruto(self):
        self.assertIn("valor_bruto = models.DecimalField", self.models)

    def test_titulo_deve_persistir_valor_desconto(self):
        self.assertIn("valor_desconto = models.DecimalField", self.models)

    def test_titulo_deve_persistir_valor_juros(self):
        self.assertIn("valor_juros = models.DecimalField", self.models)

    def test_titulo_deve_persistir_observacao(self):
        bloco = self.models[self.models.find("class TituloFinanceiro"):self.models.find("class ParcelaFinanceira")]
        self.assertIn("observacao = models.TextField", bloco)

    def test_manual_deve_receber_novos_campos(self):
        trecho=self.services[self.services.find("def criar_lancamento_manual("):]
        for nome in ("data_competencia","valor_bruto","valor_desconto","valor_juros","observacao"):
            self.assertIn(nome,trecho)

    def test_manual_deve_validar_valor_final(self):
        trecho=self.services[self.services.find("def criar_lancamento_manual("):]
        self.assertIn("valor_bruto",trecho)
        self.assertIn("valor_desconto",trecho)
        self.assertIn("valor_juros",trecho)
        self.assertIn("valor_final",trecho)

    def test_manual_deve_hardenizar_idempotencia(self):
        trecho=self.services[self.services.find("def criar_lancamento_manual("):]
        self.assertIn("conflito",trecho.lower())
        self.assertIn("chave_idempotencia",trecho)
        self.assertIn("plano_conta",trecho)
        self.assertIn("centro_custo",trecho)