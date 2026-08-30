import base64
import copy

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import Encoding
from lxml import etree

from fiscal.services_certificado_a1 import CertificadoA1


NFE_NS = "http://www.portalfiscal.inf.br/nfe"
DS_NS = "http://www.w3.org/2000/09/xmldsig#"
C14N_1_0 = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
ENVELOPED = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"
RSA_SHA1 = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
SHA1 = "http://www.w3.org/2000/09/xmldsig#sha1"


class AssinaturaXMLNFeError(ValueError):
    """Falha controlada na assinatura XML da NF-e/NFC-e."""


def _c14n(elemento) -> bytes:
    return etree.tostring(
        elemento,
        method="c14n",
        exclusive=False,
        with_comments=False,
    )


def assinar_xml_nfe(*, xml: str, certificado_a1: CertificadoA1) -> str:
    """Assina infNFe e adiciona ds:Signature como filho de NFe."""
    try:
        parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
        raiz = etree.fromstring(xml.encode("utf-8"), parser=parser)
    except Exception as exc:
        raise AssinaturaXMLNFeError("XML da NF-e invalido para assinatura.") from exc

    q = lambda ns, nome: f"{{{ns}}}{nome}"
    if raiz.tag != q(NFE_NS, "NFe"):
        raise AssinaturaXMLNFeError("Elemento raiz NFe nao encontrado.")

    inf = raiz.find(q(NFE_NS, "infNFe"))
    if inf is None:
        raise AssinaturaXMLNFeError("Elemento infNFe nao encontrado.")

    id_inf = str(inf.get("Id") or "").strip()
    if not id_inf.startswith("NFe") or len(id_inf) != 47:
        raise AssinaturaXMLNFeError("Id de infNFe invalido para assinatura.")

    if raiz.find(q(DS_NS, "Signature")) is not None:
        raise AssinaturaXMLNFeError("XML da NF-e ja possui Signature.")

    # Digest do infNFe canonico. Signature e irma de infNFe, portanto o
    # transform enveloped nao remove conteudo neste ponto.
    digest = hashes.Hash(hashes.SHA1())
    digest.update(_c14n(copy.deepcopy(inf)))
    digest_value = base64.b64encode(digest.finalize()).decode("ascii")

    signature = etree.Element(q(DS_NS, "Signature"), nsmap={"ds": DS_NS})
    signed_info = etree.SubElement(signature, q(DS_NS, "SignedInfo"))
    etree.SubElement(
        signed_info, q(DS_NS, "CanonicalizationMethod"), Algorithm=C14N_1_0
    )
    etree.SubElement(
        signed_info, q(DS_NS, "SignatureMethod"), Algorithm=RSA_SHA1
    )
    reference = etree.SubElement(
        signed_info, q(DS_NS, "Reference"), URI=f"#{id_inf}"
    )
    transforms = etree.SubElement(reference, q(DS_NS, "Transforms"))
    etree.SubElement(transforms, q(DS_NS, "Transform"), Algorithm=ENVELOPED)
    etree.SubElement(transforms, q(DS_NS, "Transform"), Algorithm=C14N_1_0)
    etree.SubElement(reference, q(DS_NS, "DigestMethod"), Algorithm=SHA1)
    etree.SubElement(reference, q(DS_NS, "DigestValue")).text = digest_value

    # Canonicalizar SignedInfo somente depois de Signature estar no contexto final.
    raiz.append(signature)
    signed_info_c14n = _c14n(signed_info)
    assinatura = certificado_a1.chave_privada.sign(
        signed_info_c14n,
        padding.PKCS1v15(),
        hashes.SHA1(),
    )
    etree.SubElement(signature, q(DS_NS, "SignatureValue")).text = (
        base64.b64encode(assinatura).decode("ascii")
    )

    key_info = etree.SubElement(signature, q(DS_NS, "KeyInfo"))
    x509_data = etree.SubElement(key_info, q(DS_NS, "X509Data"))
    cert_der = certificado_a1.certificado.public_bytes(Encoding.DER)
    etree.SubElement(x509_data, q(DS_NS, "X509Certificate")).text = (
        base64.b64encode(cert_der).decode("ascii")
    )

    return etree.tostring(
        raiz,
        encoding="unicode",
        xml_declaration=False,
    )