import base64
import datetime
import tempfile
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase
from lxml import etree

from fiscal.services_assinatura_xml import (
    C14N_1_0,
    DS_NS,
    ENVELOPED,
    NFE_NS,
    RSA_SHA1,
    SHA1,
    assinar_xml_nfe,
)
from fiscal.services_certificado_a1 import carregar_certificado_a1
from fiscal.tests.fixtures_certificado_a1 import criar_pkcs12_sintetico


class AssinaturaXMLNFCeTests(SimpleTestCase):
    CHAVE = "35260812345678000195650010000000011000000019"
    SENHA = "senha-195f3l"

    def _certificado(self, pasta):
        p = criar_pkcs12_sintetico(
            pasta,
            senha=self.SENHA,
        )
        return carregar_certificado_a1(referencia=str(p), senha=self.SENHA)

    def _xml(self):
        return (
            f'<NFe xmlns="{NFE_NS}">'
            f'<infNFe Id="NFe{self.CHAVE}" versao="4.00"><ide/></infNFe>'
            f'<infNFeSupl><qrCode>https://exemplo.invalid/?p={self.CHAVE}|3|2</qrCode>'
            f'<urlChave>https://exemplo.invalid/consulta</urlChave></infNFeSupl>'
            f'</NFe>'
        )

    def test_assina_inf_nfe_com_contrato_xml_dsig(self):
        with tempfile.TemporaryDirectory() as pasta:
            a1=self._certificado(pasta)
            xml=assinar_xml_nfe(xml=self._xml(),certificado_a1=a1)

        root=etree.fromstring(xml.encode())
        ns={"n":NFE_NS,"ds":DS_NS}
        sig=root.find("ds:Signature",ns)
        self.assertIsNotNone(sig)
        self.assertEqual(
            [etree.QName(x).localname for x in root],
            ["infNFe","infNFeSupl","Signature"],
        )
        self.assertEqual(
            sig.find("ds:SignedInfo/ds:CanonicalizationMethod",ns).get("Algorithm"),
            C14N_1_0,
        )
        self.assertEqual(
            sig.find("ds:SignedInfo/ds:SignatureMethod",ns).get("Algorithm"),
            RSA_SHA1,
        )
        ref=sig.find("ds:SignedInfo/ds:Reference",ns)
        self.assertEqual(ref.get("URI"),f"#NFe{self.CHAVE}")
        transforms=ref.findall("ds:Transforms/ds:Transform",ns)
        self.assertEqual([x.get("Algorithm") for x in transforms],[ENVELOPED,C14N_1_0])
        self.assertEqual(ref.find("ds:DigestMethod",ns).get("Algorithm"),SHA1)

    def test_digest_e_assinatura_sao_verificaveis_localmente(self):
        with tempfile.TemporaryDirectory() as pasta:
            a1=self._certificado(pasta)
            xml=assinar_xml_nfe(xml=self._xml(),certificado_a1=a1)

        root=etree.fromstring(xml.encode())
        ns={"n":NFE_NS,"ds":DS_NS}
        inf=root.find("n:infNFe",ns)
        sig=root.find("ds:Signature",ns)
        signed_info=sig.find("ds:SignedInfo",ns)

        digest=hashes.Hash(hashes.SHA1())
        digest.update(etree.tostring(inf,method="c14n",exclusive=False,with_comments=False))
        esperado=base64.b64encode(digest.finalize()).decode()
        self.assertEqual(
            sig.findtext("ds:SignedInfo/ds:Reference/ds:DigestValue",namespaces=ns),
            esperado,
        )

        assinatura=base64.b64decode(sig.findtext("ds:SignatureValue",namespaces=ns))
        a1.certificado.public_key().verify(
            assinatura,
            etree.tostring(
                signed_info,method="c14n",exclusive=False,with_comments=False
            ),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )

    def test_keyinfo_contem_apenas_certificado_final(self):
        with tempfile.TemporaryDirectory() as pasta:
            a1=self._certificado(pasta)
            xml=assinar_xml_nfe(xml=self._xml(),certificado_a1=a1)
        root=etree.fromstring(xml.encode())
        ns={"ds":DS_NS}
        self.assertEqual(len(root.findall(".//ds:X509Certificate",ns)),1)
        self.assertEqual(len(root.findall(".//ds:X509IssuerSerial",ns)),0)
        self.assertNotIn("PRIVATE KEY",xml)