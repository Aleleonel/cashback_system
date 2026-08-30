from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import (
    NFCeXMLError,
    NFE_NAMESPACE,
    adicionar_inf_nfe_supl_qrcode_v3_online,
)


class InfNFeSuplQRCodeV3Tests(SimpleTestCase):
    CHAVE = "35260812345678000195650010000000011000000019"

    def _nfe(self):
        nfe = ET.Element(f"{{{NFE_NAMESPACE}}}NFe")
        ET.SubElement(
            nfe,
            f"{{{NFE_NAMESPACE}}}infNFe",
            {"Id": f"NFe{self.CHAVE}", "versao": "4.00"},
        )
        return nfe

    def test_homologacao_sp_qrcode_v3_online(self):
        nfe = self._nfe()
        supl = adicionar_inf_nfe_supl_qrcode_v3_online(
            nfe,
            chave_acesso=self.CHAVE,
            ambiente="homologacao",
            uf="SP",
        )
        ns={"nfe": NFE_NAMESPACE}
        self.assertEqual(
            supl.findtext("nfe:qrCode", namespaces=ns),
            "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode"
            f"?p={self.CHAVE}|3|2",
        )
        self.assertEqual(
            supl.findtext("nfe:urlChave", namespaces=ns),
            "https://www.homologacao.nfce.fazenda.sp.gov.br/consulta",
        )
        self.assertEqual(
            [node.tag.rsplit("}", 1)[-1] for node in list(nfe)],
            ["infNFe", "infNFeSupl"],
        )

    def test_producao_sp_qrcode_v3_online(self):
        nfe=self._nfe()
        supl=adicionar_inf_nfe_supl_qrcode_v3_online(
            nfe, chave_acesso=self.CHAVE, ambiente="producao", uf="SP"
        )
        ns={"nfe": NFE_NAMESPACE}
        self.assertEqual(
            supl.findtext("nfe:qrCode", namespaces=ns),
            "https://www.nfce.fazenda.sp.gov.br/qrcode"
            f"?p={self.CHAVE}|3|1",
        )

    def test_nao_adiciona_csc_idcsc_ou_assinatura_qr(self):
        nfe=self._nfe()
        adicionar_inf_nfe_supl_qrcode_v3_online(
            nfe, chave_acesso=self.CHAVE, ambiente="homologacao", uf="SP"
        )
        xml=ET.tostring(nfe, encoding="unicode")
        self.assertNotIn("CSC", xml)
        self.assertNotIn("idCSC", xml)
        self.assertNotIn("assinatura", xml)

    def test_rejeita_uf_ainda_nao_configurada(self):
        with self.assertRaises(NFCeXMLError):
            adicionar_inf_nfe_supl_qrcode_v3_online(
                self._nfe(),
                chave_acesso=self.CHAVE,
                ambiente="homologacao",
                uf="RJ",
            )