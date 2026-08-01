from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from pdv.choices import StatusOperacaoVenda, TipoEmissaoVenda
from pdv.models import Venda


class MotorFinalizacaoEstruturaTests(SimpleTestCase):
    def test_tipo_emissao_possui_opcoes_previstas(self):
        self.assertEqual(TipoEmissaoVenda.NAO_FISCAL, "nao_fiscal")
        self.assertEqual(TipoEmissaoVenda.FISCAL, "fiscal")

    def test_modelo_finalizado_exige_vendedor(self):
        venda = Venda(
            status=StatusOperacaoVenda.FINALIZADA,
            subtotal=Decimal("0.00"),
            desconto=Decimal("0.00"),
            acrescimo=Decimal("0.00"),
            total=Decimal("0.00"),
        )

        with self.assertRaises(ValidationError) as contexto:
            venda.clean()

        self.assertIn("vendedor", contexto.exception.message_dict)
