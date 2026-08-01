from pathlib import Path

from django.test import SimpleTestCase


class VoucherClienteContratoTests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.views = (root / "pdv" / "views.py").read_text(encoding="utf-8-sig")

    def test_nao_usa_voucher_generico(self):
        self.assertNotIn("get_melhor_voucher(", self.views)

    def test_sugestao_exige_cliente_da_venda(self):
        self.assertIn("if voucher.cliente_id == venda.cliente_id", self.views)

    def test_validacao_manual_permanece(self):
        self.assertIn("def validar_voucher_venda_web", self.views)
