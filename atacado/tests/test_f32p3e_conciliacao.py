from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from atacado.integracao_totais import conciliar_total_pedido


class ConciliacaoMonetariaF32P3ETests(SimpleTestCase):
    def test_valores_exatos(self):
        self.assertEqual(conciliar_total_pedido(subtotal_itens="100.00", desconto="10.00", acrescimo="5.00", total_pedido="95.00"), Decimal("95.00"))

    def test_divergencia_de_um_centavo(self):
        with self.assertRaises(ValidationError):
            conciliar_total_pedido(subtotal_itens="100.00", desconto="0.00", acrescimo="0.00", total_pedido="99.99")

    def test_valor_negativo(self):
        with self.assertRaises(ValidationError):
            conciliar_total_pedido(subtotal_itens="-1.00", desconto="0.00", acrescimo="0.00", total_pedido="0.00")

    def test_casas_decimais_invalidas(self):
        with self.assertRaises(ValidationError):
            conciliar_total_pedido(subtotal_itens="1.001", desconto="0.00", acrescimo="0.00", total_pedido="1.00")

    def test_nan_invalido(self):
        with self.assertRaises(ValidationError):
            conciliar_total_pedido(subtotal_itens="NaN", desconto="0.00", acrescimo="0.00", total_pedido="0.00")
