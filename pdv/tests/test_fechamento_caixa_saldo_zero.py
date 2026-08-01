
from pathlib import Path

from django.test import SimpleTestCase


class FechamentoCaixaSaldoZeroContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = Path(
            "pdv/services/vendas/caixa.py"
        ).read_text(encoding="utf-8")

    def test_movimento_so_e_criado_com_valor_positivo(self):
        self.assertIn(
            'if valor_calculado > Decimal("0.00"):',
            self.service,
        )
        self.assertIn(
            "MovimentacaoCaixa.objects.create(**kwargs)",
            self.service,
        )

    def test_saldo_zero_nao_quebra_auditoria(self):
        self.assertIn("movimento = None", self.service)
        self.assertIn(
            '"nao_gerado_saldo_zero"',
            self.service,
        )
        self.assertIn(
            "movimento={movimento_id}",
            self.service,
        )

    def test_fechamento_permanece_transacional(self):
        self.assertIn(
            "def fechar_sessao_caixa(",
            self.service,
        )
        self.assertIn("select_for_update", self.service)
        self.assertIn("transaction.atomic", self.service)
