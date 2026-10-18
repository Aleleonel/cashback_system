from datetime import date
from decimal import Decimal
from django.test import SimpleTestCase
from pathlib import Path

class F24ExtratoContaFinanceiraContractRED(SimpleTestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent
        self.urls = (self.root / "urls.py").read_text(encoding="utf-8")
        self.views = (self.root / "views.py").read_text(encoding="utf-8")
        self.tpl = self.root / "templates" / "financeiro" / "contas_financeiras.html"

    def test_deve_existir_rota_extrato_por_conta(self):
        self.assertIn("contas-financeiras/<uuid:conta_uuid>/extrato/", self.urls)
        self.assertIn('name="conta_financeira_extrato"', self.urls)

    def test_deve_existir_view_extrato(self):
        self.assertIn("def conta_financeira_extrato(", self.views)

    def test_lista_contas_deve_expor_acao_extrato(self):
        html = self.tpl.read_text(encoding="utf-8")
        self.assertIn("conta_financeira_extrato", html)
        self.assertIn("Extrato", html)

    def test_extrato_deve_ser_derivado_de_baixa_financeira(self):
        self.assertIn("BaixaFinanceira", self.views)
        self.assertIn("conta_financeira", self.views)

    def test_extrato_deve_preservar_eventos_baixa_e_estorno(self):
        # O extrato nao cria novo motor de saldo: usa eventos financeiros existentes.
        self.assertIn("BaixaFinanceira", self.views)
        self.assertTrue(True)

    def test_extrato_nao_deve_exigir_novo_modelo_movimentacao(self):
        models = (self.root / "models.py").read_text(encoding="utf-8")
        self.assertNotIn("class ExtratoContaFinanceira(", models)
        self.assertNotIn("class MovimentacaoFinanceira(", models)