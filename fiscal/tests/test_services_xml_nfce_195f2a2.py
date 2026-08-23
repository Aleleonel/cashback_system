from decimal import Decimal
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import (
    NFE_NAMESPACE,
    NFCeXMLError,
    adicionar_icms_item_nfce,
)

NS = {"nfe": NFE_NAMESPACE}


def _item(**overrides):
    dados = {
        "origem_mercadoria_codigo": "0",
        "cst_icms_codigo": "00",
        "csosn_codigo": "",
        "regime_tributario": "normal",
        "modalidade_base_icms": "3",
        "base_icms": Decimal("10.00"),
        "aliquota_icms": Decimal("18.0000"),
        "valor_icms": Decimal("1.80"),
    }
    dados.update(overrides)
    return SimpleNamespace(**dados)


def _imposto():
    return ET.Element(f"{{{NFE_NAMESPACE}}}imposto")


class NFCeXML195F2A2Tests(SimpleTestCase):

    def test_icms00_serializa_campos_do_snapshot(self):
        imposto = _imposto()

        adicionar_icms_item_nfce(imposto, item=_item())

        icms00 = imposto.find("nfe:ICMS/nfe:ICMS00", NS)

        self.assertIsNotNone(icms00)
        self.assertEqual(
            icms00.findtext("nfe:orig", namespaces=NS),
            "0",
        )
        self.assertEqual(
            icms00.findtext("nfe:CST", namespaces=NS),
            "00",
        )
        self.assertEqual(
            icms00.findtext("nfe:modBC", namespaces=NS),
            "3",
        )
        self.assertEqual(
            icms00.findtext("nfe:vBC", namespaces=NS),
            "10.00",
        )
        self.assertEqual(
            icms00.findtext("nfe:pICMS", namespaces=NS),
            "18.0000",
        )
        self.assertEqual(
            icms00.findtext("nfe:vICMS", namespaces=NS),
            "1.80",
        )

    def test_nao_recalcula_valor_icms(self):
        imposto = _imposto()

        adicionar_icms_item_nfce(
            imposto,
            item=_item(
                base_icms=Decimal("100.00"),
                aliquota_icms=Decimal("18.0000"),
                valor_icms=Decimal("7.77"),
            ),
        )

        icms00 = imposto.find("nfe:ICMS/nfe:ICMS00", NS)

        self.assertEqual(
            icms00.findtext("nfe:vICMS", namespaces=NS),
            "7.77",
        )

    def test_item_sem_classificacao_icms_preserva_imposto_vazio(self):
        imposto = _imposto()

        resultado = adicionar_icms_item_nfce(
            imposto,
            item=SimpleNamespace(),
        )

        self.assertIsNone(resultado)
        self.assertEqual(len(imposto), 0)

    def test_rejeita_cst_e_csosn_simultaneos(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_icms_item_nfce(
                _imposto(),
                item=_item(csosn_codigo="102"),
            )

    def test_rejeita_csosn_nesta_etapa(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_icms_item_nfce(
                _imposto(),
                item=_item(
                    cst_icms_codigo="",
                    csosn_codigo="102",
                    regime_tributario="simples",
                ),
            )

    def test_rejeita_cst_diferente_de_00(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_icms_item_nfce(
                _imposto(),
                item=_item(cst_icms_codigo="20"),
            )

    def test_rejeita_origem_invalida(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_icms_item_nfce(
                _imposto(),
                item=_item(origem_mercadoria_codigo="9"),
            )

    def test_rejeita_modbc_invalido(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_icms_item_nfce(
                _imposto(),
                item=_item(modalidade_base_icms="9"),
            )

    def test_rejeita_aliquota_ausente(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_icms_item_nfce(
                _imposto(),
                item=_item(aliquota_icms=None),
            )
