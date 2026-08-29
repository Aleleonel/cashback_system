from decimal import Decimal
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import (
    adicionar_icms_item_nfce,
    adicionar_total_nfce,
)


def local(tag):
    return tag.split("}", 1)[-1]


def child(parent, name):
    if parent is None:
        return None
    return next((x for x in list(parent) if local(x.tag) == name), None)


def value(parent, name):
    node = child(parent, name)
    return None if node is None else node.text


class XMLNFCeFCP195F2C3Tests(SimpleTestCase):
    def item(self, **kw):
        data = dict(
            regime_tributario="normal",
            cst_icms_codigo="00",
            csosn_codigo="",
            origem_mercadoria_codigo="0",
            modalidade_base_icms="3",
            base_icms=Decimal("100.00"),
            aliquota_icms=Decimal("18.0000"),
            valor_icms=Decimal("18.00"),
            base_fcp=Decimal("100.00"),
            aliquota_fcp=Decimal("2.0000"),
            valor_fcp=Decimal("2.00"),
            valor_produtos=Decimal("100.00"),
            desconto=Decimal("0.00"),
            frete=Decimal("0.00"),
            seguro=Decimal("0.00"),
            outras_despesas=Decimal("0.00"),
            valor_pis=Decimal("1.65"),
            valor_cofins=Decimal("7.60"),
        )
        data.update(kw)
        return SimpleNamespace(**data)

    def test_icms00_serializa_fcp_congelado_sem_recalcular(self):
        item = self.item(valor_fcp=Decimal("1.23"))
        icms00 = adicionar_icms_item_nfce(
            ET.Element("imposto"),
            item=item,
        )

        self.assertIsNone(child(icms00, "vBCFCP"))
        self.assertEqual(value(icms00, "pFCP"), "2.0000")
        self.assertEqual(value(icms00, "vFCP"), "1.23")

    def test_icms00_sem_fcp_omite_campos_fcp(self):
        item = self.item(
            base_fcp=Decimal("0.00"),
            aliquota_fcp=None,
            valor_fcp=Decimal("0.00"),
        )
        icms00 = adicionar_icms_item_nfce(
            ET.Element("imposto"),
            item=item,
        )

        self.assertIsNone(child(icms00, "vBCFCP"))
        self.assertIsNone(child(icms00, "pFCP"))
        self.assertIsNone(child(icms00, "vFCP"))

    def test_total_vfcp_soma_valores_congelados(self):
        inf_nfe = ET.Element("infNFe")

        itens = [
            self.item(valor_fcp=Decimal("2.00")),
            self.item(
                valor_produtos=Decimal("50.00"),
                base_icms=Decimal("50.00"),
                valor_icms=Decimal("9.00"),
                base_fcp=Decimal("50.00"),
                valor_fcp=Decimal("1.00"),
                valor_pis=Decimal("0.83"),
                valor_cofins=Decimal("3.80"),
            ),
        ]

        adicionar_total_nfce(inf_nfe, itens=itens)

        total = child(inf_nfe, "total")
        icms_tot = child(total, "ICMSTot")

        self.assertIsNotNone(icms_tot)
        self.assertEqual(value(icms_tot, "vFCP"), "3.00")
        self.assertEqual(value(icms_tot, "vFCPST"), "0.00")
        self.assertEqual(value(icms_tot, "vFCPSTRet"), "0.00")
