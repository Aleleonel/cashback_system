from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from pdv.models import ItemVenda


class ItemVendaCalculosTests(SimpleTestCase):
    def test_calcula_subtotal_e_total(self):
        item = ItemVenda(
            quantidade=Decimal("2.500"),
            preco_unitario=Decimal("10.00"),
            desconto=Decimal("2.00"),
            acrescimo=Decimal("1.00"),
        )
        item.recalcular()
        self.assertEqual(item.subtotal, Decimal("25.00"))
        self.assertEqual(item.total, Decimal("24.00"))

    def test_desconto_nao_pode_tornar_total_negativo(self):
        item = ItemVenda(
            quantidade=Decimal("1.000"),
            preco_unitario=Decimal("10.00"),
            desconto=Decimal("11.00"),
            acrescimo=Decimal("0.00"),
        )
        item.recalcular()
        with self.assertRaises(ValidationError):
            item.clean()

    def test_quantidade_precisa_ser_positiva(self):
        item = ItemVenda(
            quantidade=Decimal("0.000"),
            preco_unitario=Decimal("10.00"),
            desconto=Decimal("0.00"),
            acrescimo=Decimal("0.00"),
        )
        item.recalcular()
        with self.assertRaises(ValidationError):
            item.clean()

    def test_delete_fisico_e_bloqueado(self):
        with self.assertRaises(ValidationError):
            ItemVenda().delete()
