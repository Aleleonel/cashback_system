from dataclasses import dataclass

from lxml import etree


NFE_NS = "http://www.portalfiscal.inf.br/nfe"
NS = {"nfe": NFE_NS}


class AutorizacaoXMLNFCeError(ValueError):
    pass


@dataclass(frozen=True)
class RetornoAutorizacaoNFCe:
    codigo_status: str
    motivo_status: str
    protocolo: str = ""
    numero_recibo: str = ""
    data_recebimento: str = ""
    chave_acesso: str = ""
    ambiente: str = ""
    versao_aplicacao: str = ""
    xml_protocolo: str = ""

    @property
    def autorizado(self):
        return self.codigo_status == "100"


def montar_envi_nfe(*, xml_assinado: str, id_lote: str, ind_sinc: int = 1) -> str:
    lote = str(id_lote or "").strip()
    if not lote or not lote.isdigit() or len(lote) > 15:
        raise AutorizacaoXMLNFCeError("idLote deve conter de 1 a 15 digitos.")
    if ind_sinc not in (0, 1):
        raise AutorizacaoXMLNFCeError("indSinc deve ser 0 ou 1.")

    try:
        nfe = etree.fromstring(str(xml_assinado or "").encode("utf-8"))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise AutorizacaoXMLNFCeError("XML assinado invalido.") from exc

    if nfe.tag != f"{{{NFE_NS}}}NFe":
        raise AutorizacaoXMLNFCeError("XML assinado deve possuir raiz NFe.")

    raiz = etree.Element(f"{{{NFE_NS}}}enviNFe", versao="4.00", nsmap={None: NFE_NS})
    etree.SubElement(raiz, f"{{{NFE_NS}}}idLote").text = lote
    etree.SubElement(raiz, f"{{{NFE_NS}}}indSinc").text = str(ind_sinc)
    raiz.append(nfe)
    return etree.tostring(raiz, encoding="unicode", xml_declaration=False)


def interpretar_ret_envi_nfe(*, xml_retorno: str) -> RetornoAutorizacaoNFCe:
    try:
        raiz = etree.fromstring(str(xml_retorno or "").encode("utf-8"))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise AutorizacaoXMLNFCeError("XML de retorno da SEFAZ invalido.") from exc

    if raiz.tag != f"{{{NFE_NS}}}retEnviNFe":
        raise AutorizacaoXMLNFCeError("Retorno deve possuir raiz retEnviNFe.")

    codigo_lote = (raiz.findtext("nfe:cStat", namespaces=NS) or "").strip()
    motivo_lote = (raiz.findtext("nfe:xMotivo", namespaces=NS) or "").strip()
    numero_recibo = (raiz.findtext("nfe:infRec/nfe:nRec", namespaces=NS) or "").strip()

    prot = raiz.find("nfe:protNFe", namespaces=NS)
    if prot is None:
        return RetornoAutorizacaoNFCe(
            codigo_status=codigo_lote,
            motivo_status=motivo_lote,
            numero_recibo=numero_recibo,
        )

    inf = prot.find("nfe:infProt", namespaces=NS)
    if inf is None:
        raise AutorizacaoXMLNFCeError("protNFe sem infProt.")

    codigo = (inf.findtext("nfe:cStat", namespaces=NS) or "").strip()
    motivo = (inf.findtext("nfe:xMotivo", namespaces=NS) or "").strip()
    protocolo = (inf.findtext("nfe:nProt", namespaces=NS) or "").strip()
    data_recebimento = (inf.findtext("nfe:dhRecbto", namespaces=NS) or "").strip()
    chave_acesso = (inf.findtext("nfe:chNFe", namespaces=NS) or "").strip()
    ambiente = (inf.findtext("nfe:tpAmb", namespaces=NS) or "").strip()
    versao_aplicacao = (inf.findtext("nfe:verAplic", namespaces=NS) or "").strip()
    xml_protocolo = etree.tostring(prot, encoding="unicode", xml_declaration=False)
    if codigo == "100":
        ausentes = []
        if not chave_acesso: ausentes.append("chNFe")
        if not data_recebimento: ausentes.append("dhRecbto")
        if not protocolo: ausentes.append("nProt")
        if not ambiente: ausentes.append("tpAmb")
        if not versao_aplicacao: ausentes.append("verAplic")
        if ausentes:
            raise AutorizacaoXMLNFCeError("Retorno autorizado incompleto: " + ", ".join(ausentes) + ".")
        if len(chave_acesso) != 44 or not chave_acesso.isdigit():
            raise AutorizacaoXMLNFCeError("Retorno autorizado possui chNFe invalida.")
        if ambiente not in ("1", "2"):
            raise AutorizacaoXMLNFCeError("Retorno autorizado possui tpAmb invalido.")
    return RetornoAutorizacaoNFCe(codigo_status=codigo, motivo_status=motivo, protocolo=protocolo, data_recebimento=data_recebimento, chave_acesso=chave_acesso, numero_recibo=numero_recibo, ambiente=ambiente, versao_aplicacao=versao_aplicacao, xml_protocolo=xml_protocolo)


def montar_nfe_proc(*, xml_assinado: str, xml_protocolo: str) -> str:
    try:
        nfe = etree.fromstring(str(xml_assinado or "").encode("utf-8"))
        prot = etree.fromstring(str(xml_protocolo or "").encode("utf-8"))
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise AutorizacaoXMLNFCeError("XML NFe/protocolo invalido para nfeProc.") from exc

    if nfe.tag != f"{{{NFE_NS}}}NFe" or prot.tag != f"{{{NFE_NS}}}protNFe":
        raise AutorizacaoXMLNFCeError("nfeProc exige NFe e protNFe.")
    inf_nfe = nfe.find("nfe:infNFe", namespaces=NS)
    inf_prot = prot.find("nfe:infProt", namespaces=NS)
    if inf_nfe is None or inf_prot is None:
        raise AutorizacaoXMLNFCeError("nfeProc exige infNFe e infProt.")
    id_nfe = (inf_nfe.get("Id") or "").strip()
    chave_nfe = id_nfe[3:] if id_nfe.startswith("NFe") else ""
    chave_protocolo = (inf_prot.findtext("nfe:chNFe", namespaces=NS) or "").strip()
    codigo_protocolo = (inf_prot.findtext("nfe:cStat", namespaces=NS) or "").strip()
    numero_protocolo = (inf_prot.findtext("nfe:nProt", namespaces=NS) or "").strip()
    if len(chave_nfe) != 44 or not chave_nfe.isdigit():
        raise AutorizacaoXMLNFCeError("infNFe possui chave de acesso invalida.")
    if chave_protocolo != chave_nfe:
        raise AutorizacaoXMLNFCeError("Chave do protocolo difere da chave da NFe.")
    if codigo_protocolo != "100":
        raise AutorizacaoXMLNFCeError("nfeProc exige protocolo de autorizacao cStat 100.")
    if not numero_protocolo:
        raise AutorizacaoXMLNFCeError("nfeProc exige numero de protocolo de autorizacao.")
    raiz = etree.Element(f"{{{NFE_NS}}}nfeProc", versao="4.00", nsmap={None: NFE_NS})
    raiz.append(nfe)
    raiz.append(prot)
    return etree.tostring(raiz, encoding="unicode", xml_declaration=False)