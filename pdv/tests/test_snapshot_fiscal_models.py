from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from pdv.choices import StatusOperacaoVenda
from pdv.models import ItemVendaFiscal, VendaFiscal


class SnapshotFiscalEstruturaTests(TestCase):
    def test_models_estao_registrados_no_app_pdv(self):
        self.assertEqual(VendaFiscal._meta.app_label, "pdv")
        self.assertEqual(ItemVendaFiscal._meta.app_label, "pdv")

    def test_related_names_fiscais(self):
        self.assertEqual(
            VendaFiscal._meta.get_field("venda").remote_field.related_name,
            "fiscal",
        )
        self.assertEqual(
            ItemVendaFiscal._meta.get_field("item_venda").remote_field.related_name,
            "fiscal",
        )

    def test_precisoes_principais(self):
        quantidade = ItemVendaFiscal._meta.get_field("quantidade")
        valor = ItemVendaFiscal._meta.get_field("valor_icms")
        aliquota = ItemVendaFiscal._meta.get_field("aliquota_icms")

        self.assertEqual((quantidade.max_digits, quantidade.decimal_places), (14, 3))
        self.assertEqual((valor.max_digits, valor.decimal_places), (14, 2))
        self.assertEqual((aliquota.max_digits, aliquota.decimal_places), (9, 4))


class SnapshotFiscalValidacaoModelTests(TestCase):
    def test_venda_fiscal_rejeita_total_negativo_em_full_clean(self):
        snapshot = VendaFiscal(
            venda_id=999999,
            regime_tributario="simples_nacional",
            uf_origem="SP",
            uf_destino="SP",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            total_tributos=Decimal("-0.01"),
        )

        with self.assertRaises(ValidationError):
            snapshot.full_clean(exclude={"venda"})

    def test_item_fiscal_rejeita_reducao_acima_de_cem(self):
        snapshot = ItemVendaFiscal(
            item_venda_id=999999,
            regime_tributario="simples_nacional",
            uf_origem="SP",
            uf_destino="SP",
            tipo_operacao="saida",
            finalidade_operacao="venda",
            quantidade=Decimal("1.000"),
            valor_unitario=Decimal("10.00"),
            valor_produtos=Decimal("10.00"),
            percentual_reducao_base_icms=Decimal("100.0001"),
        )

        with self.assertRaises(ValidationError):
            snapshot.full_clean(exclude={"item_venda"})

    def test_item_fiscal_aceita_aliquota_nula(self):
        campo = ItemVendaFiscal._meta.get_field("aliquota_icms")
        self.assertTrue(campo.null)
        self.assertTrue(campo.blank)