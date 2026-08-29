from decimal import Decimal
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import (
    NFE_NAMESPACE,
    NFCeXMLError,
    adicionar_cofins_item_nfce,
    adicionar_pis_item_nfce,
    adicionar_total_nfce,
    criar_envelope_nfce,
)

NS = {"nfe": NFE_NAMESPACE}

def _imposto():
    return ET.Element(f"{{{NFE_NAMESPACE}}}imposto")

def _item_pis(**overrides):
    data = dict(cst_pis_codigo="01", base_pis=Decimal("100.00"), aliquota_pis=Decimal("1.6500"), valor_pis=Decimal("1.65"))
    data.update(overrides)
    return SimpleNamespace(**data)

def _item_cofins(**overrides):
    data = dict(cst_cofins_codigo="01", base_cofins=Decimal("100.00"), aliquota_cofins=Decimal("7.6000"), valor_cofins=Decimal("7.60"))
    data.update(overrides)
    return SimpleNamespace(**data)

class PISCOFINSCST01195F2B2Tests(SimpleTestCase):
    def test_pis_cst01_serializa_snapshot(self):
        imposto = _imposto()
        adicionar_pis_item_nfce(imposto, item=_item_pis())
        grupo = imposto.find("nfe:PIS/nfe:PISAliq", NS)
        self.assertEqual(grupo.findtext("nfe:CST", namespaces=NS), "01")
        self.assertEqual(grupo.findtext("nfe:vBC", namespaces=NS), "100.00")
        self.assertEqual(grupo.findtext("nfe:pPIS", namespaces=NS), "1.6500")
        self.assertEqual(grupo.findtext("nfe:vPIS", namespaces=NS), "1.65")

    def test_cofins_cst01_serializa_snapshot(self):
        imposto = _imposto()
        adicionar_cofins_item_nfce(imposto, item=_item_cofins())
        grupo = imposto.find("nfe:COFINS/nfe:COFINSAliq", NS)
        self.assertEqual(grupo.findtext("nfe:CST", namespaces=NS), "01")
        self.assertEqual(grupo.findtext("nfe:vBC", namespaces=NS), "100.00")
        self.assertEqual(grupo.findtext("nfe:pCOFINS", namespaces=NS), "7.6000")
        self.assertEqual(grupo.findtext("nfe:vCOFINS", namespaces=NS), "7.60")

    def test_nao_recalcula_valores(self):
        pis = _imposto()
        adicionar_pis_item_nfce(pis, item=_item_pis(valor_pis=Decimal("9.99")))
        self.assertEqual(pis.findtext("nfe:PIS/nfe:PISAliq/nfe:vPIS", namespaces=NS), "9.99")
        cofins = _imposto()
        adicionar_cofins_item_nfce(cofins, item=_item_cofins(valor_cofins=Decimal("8.88")))
        self.assertEqual(cofins.findtext("nfe:COFINS/nfe:COFINSAliq/nfe:vCOFINS", namespaces=NS), "8.88")

    def test_item_legado_sem_cst_omite_grupos(self):
        imposto = _imposto()
        item = SimpleNamespace()
        self.assertIsNone(adicionar_pis_item_nfce(imposto, item=item))
        self.assertIsNone(adicionar_cofins_item_nfce(imposto, item=item))
        self.assertIsNone(imposto.find("nfe:PIS", NS))
        self.assertIsNone(imposto.find("nfe:COFINS", NS))

    def test_cst_nao_suportado_falha_explicitamente(self):
        with self.assertRaisesRegex(NFCeXMLError, "CST PIS 04"):
            adicionar_pis_item_nfce(_imposto(), item=_item_pis(cst_pis_codigo="04"))
        with self.assertRaisesRegex(NFCeXMLError, "CST COFINS 04"):
            adicionar_cofins_item_nfce(_imposto(), item=_item_cofins(cst_cofins_codigo="04"))

    def test_campos_obrigatorios_no_cst01(self):
        with self.assertRaisesRegex(NFCeXMLError, "Base PIS"):
            adicionar_pis_item_nfce(_imposto(), item=_item_pis(base_pis=None))
        with self.assertRaisesRegex(NFCeXMLError, "Aliquota COFINS"):
            adicionar_cofins_item_nfce(_imposto(), item=_item_cofins(aliquota_cofins=None))

