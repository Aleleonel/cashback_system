from decimal import Decimal
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import (
    NFE_NAMESPACE,
    NFE_VERSION,
    NFCeXMLError,
    format_decimal,
    gerar_xml_nfce_basico,
)


class NFCeXMLBasicoTests(SimpleTestCase):

    CHAVE = "35260812345678000199650010000001231123456780"

    def test_gera_raiz_nfe_com_namespace_oficial(self):
        xml = gerar_xml_nfce_basico(self.CHAVE)
        root = ET.fromstring(xml)

        self.assertEqual(
            root.tag,
            f"{{{NFE_NAMESPACE}}}NFe",
        )

    def test_inf_nfe_possui_versao_400(self):
        xml = gerar_xml_nfce_basico(self.CHAVE)
        root = ET.fromstring(xml)

        inf_nfe = root.find(
            f"{{{NFE_NAMESPACE}}}infNFe"
        )

        self.assertIsNotNone(inf_nfe)
        self.assertEqual(
            inf_nfe.attrib["versao"],
            NFE_VERSION,
        )

    def test_id_e_nfe_mais_chave_acesso(self):
        xml = gerar_xml_nfce_basico(self.CHAVE)
        root = ET.fromstring(xml)

        inf_nfe = root.find(
            f"{{{NFE_NAMESPACE}}}infNFe"
        )

        self.assertEqual(
            inf_nfe.attrib["Id"],
            f"NFe{self.CHAVE}",
        )

        self.assertEqual(
            len(inf_nfe.attrib["Id"]),
            47,
        )

    def test_rejeita_chave_com_tamanho_invalido(self):
        with self.assertRaises(NFCeXMLError):
            gerar_xml_nfce_basico("123")

    def test_rejeita_chave_nao_numerica(self):
        with self.assertRaises(NFCeXMLError):
            gerar_xml_nfce_basico("A" * 44)

    def test_format_decimal_duas_casas(self):
        self.assertEqual(
            format_decimal(Decimal("10")),
            "10.00",
        )

        self.assertEqual(
            format_decimal(Decimal("10.5")),
            "10.50",
        )

        self.assertEqual(
            format_decimal(Decimal("10.567")),
            "10.57",
        )

    def test_format_decimal_quatro_casas(self):
        self.assertEqual(
            format_decimal(Decimal("2.5"), casas=4),
            "2.5000",
        )
