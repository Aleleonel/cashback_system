from pathlib import Path
from django.test import SimpleTestCase


class R20VendaContasReceberContratoRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]
        cls.finalizacao = (root / "pdv" / "services" / "vendas" / "finalizacao.py").read_text(encoding="utf-8")
        cls.financeiro_services = (root / "financeiro" / "services.py").read_text(encoding="utf-8")

    def test_finalizacao_possui_integracao_explicitamente_financeira(self):
        self.assertIn("gerar_contas_receber_venda", self.finalizacao)

    def test_integracao_respeita_flag_gera_contas_receber(self):
        self.assertIn("gera_contas_receber", self.finalizacao)

    def test_integracao_usa_origem_venda_pagamento(self):
        self.assertIn("VENDA_PAGAMENTO", self.finalizacao)

    def test_integracao_reusa_servico_central_de_criacao_titulo(self):
        self.assertIn("criar_titulo_financeiro", self.finalizacao)

    def test_integracao_define_idempotencia_por_pagamento(self):
        self.assertIn("chave_idempotencia", self.finalizacao)

    def test_integracao_constroi_parcelas_financeiras(self):
        self.assertIn("vencimento", self.finalizacao)
        self.assertIn("parcelas", self.finalizacao)

    def test_integracao_permanece_dentro_da_finalizacao_atomica(self):
        inicio = self.finalizacao.index("def finalizar_venda(")
        corpo = self.finalizacao[inicio:]
        self.assertIn("gerar_contas_receber_venda", corpo)

    def test_nucleo_financeiro_ja_suporta_criacao_idempotente(self):
        self.assertIn("def criar_titulo_financeiro(", self.financeiro_services)
        self.assertIn("chave_idempotencia", self.financeiro_services)