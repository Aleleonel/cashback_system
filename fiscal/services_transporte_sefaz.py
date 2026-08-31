import os
import socket
import ssl
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable
from cryptography.hazmat.primitives import serialization
from lxml import etree

SOAP12_NS = "http://www.w3.org/2003/05/soap-envelope"
WSDL_NS = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"
NFE_NS = "http://www.portalfiscal.inf.br/nfe"
SOAP_ACTION = WSDL_NS + "/nfeAutorizacaoLote"
ENDPOINTS_SP = {"homologacao":"https://homologacao.nfce.fazenda.sp.gov.br/ws/NFeAutorizacao4.asmx","producao":"https://nfce.fazenda.sp.gov.br/ws/NFeAutorizacao4.asmx"}

class TransporteSefazError(Exception):
    pass

@dataclass(frozen=True)
class RespostaTransporteSefaz:
    xml_retorno: str
    http_status: int

def endpoint_autorizacao_nfce_sp(ambiente: str) -> str:
    if ambiente not in ENDPOINTS_SP:
        raise TransporteSefazError("Ambiente SEFAZ invalido.")
    return ENDPOINTS_SP[ambiente]

def montar_envelope_soap12_autorizacao(xml_envi_nfe: str) -> bytes:
    try:
        envi=etree.fromstring(xml_envi_nfe.encode("utf-8"))
    except (etree.XMLSyntaxError,UnicodeError) as exc:
        raise TransporteSefazError("enviNFe invalido.") from exc
    q=etree.QName(envi)
    if q.namespace!=NFE_NS or q.localname!="enviNFe":
        raise TransporteSefazError("Raiz esperada: enviNFe.")
    env=etree.Element(etree.QName(SOAP12_NS,"Envelope"),nsmap={"soap12":SOAP12_NS})
    body=etree.SubElement(env,etree.QName(SOAP12_NS,"Body"))
    msg=etree.SubElement(body,etree.QName(WSDL_NS,"nfeDadosMsg"),nsmap={None:WSDL_NS})
    msg.append(envi)
    return etree.tostring(env,xml_declaration=True,encoding="utf-8")

def extrair_ret_envi_nfe(xml_soap: bytes) -> str:
    try:
        root=etree.fromstring(xml_soap)
    except etree.XMLSyntaxError as exc:
        raise TransporteSefazError("Resposta SOAP XML invalida.") from exc
    fault=root.xpath("//*[local-name()='Fault']")
    if fault:
        textos=root.xpath("//*[local-name()='Text' or local-name()='faultstring']/text()")
        raise TransporteSefazError("SEFAZ SOAP Fault: "+(textos[0].strip() if textos else "SOAP Fault"))
    retornos=root.xpath("//*[local-name()='retEnviNFe' and namespace-uri()=$ns]",ns=NFE_NS)
    if len(retornos)!=1:
        raise TransporteSefazError("Resposta SOAP sem retEnviNFe unico.")
    return etree.tostring(retornos[0],encoding="unicode")

def _ssl_contexto_a1(certificado_a1) -> ssl.SSLContext:
    key_pem=certificado_a1.chave_privada.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
    cert_pem=certificado_a1.certificado.public_bytes(serialization.Encoding.PEM)
    adicionais = getattr(certificado_a1, "certificados_adicionais", ()) or ()
    cert_pem += b"".join(certificado.public_bytes(serialization.Encoding.PEM) for certificado in adicionais)
    kp=cp=None
    try:
        k=tempfile.NamedTemporaryFile(prefix="nfce_tls_key_",suffix=".pem",delete=False)
        c=tempfile.NamedTemporaryFile(prefix="nfce_tls_cert_",suffix=".pem",delete=False)
        kp,cp=k.name,c.name;k.write(key_pem);c.write(cert_pem);k.close();c.close()
        ctx=ssl.create_default_context();ctx.minimum_version=ssl.TLSVersion.TLSv1_2;ctx.load_cert_chain(certfile=cp,keyfile=kp)
        return ctx
    finally:
        if kp and os.path.exists(kp): os.remove(kp)
        if cp and os.path.exists(cp): os.remove(cp)

def transmitir_autorizacao_nfce_sp(*,xml_envi_nfe:str,ambiente:str,certificado_a1,timeout:float=30.0,opener:Callable=urllib.request.urlopen)->RespostaTransporteSefaz:
    soap=montar_envelope_soap12_autorizacao(xml_envi_nfe)
    ctx=_ssl_contexto_a1(certificado_a1)
    ct='application/soap+xml; charset=utf-8; action="'+SOAP_ACTION+'"'
    req=urllib.request.Request(endpoint_autorizacao_nfce_sp(ambiente),data=soap,headers={"Content-Type":ct},method="POST")
    try:
        with opener(req,context=ctx,timeout=timeout) as response:
            status=int(getattr(response,"status",200));payload=response.read()
    except urllib.error.HTTPError as exc:
        try:
            payload = exc.read()
        except Exception:
            payload = b""
        if payload:
            try:
                xml_retorno = extrair_ret_envi_nfe(payload)
            except TransporteSefazError:
                pass
            else:
                return RespostaTransporteSefaz(xml_retorno, int(exc.code))
        raise TransporteSefazError("Erro HTTP SEFAZ: "+str(exc.code)) from exc
    except (urllib.error.URLError,TimeoutError,socket.timeout) as exc:
        raise TransporteSefazError("Falha de comunicacao com a SEFAZ.") from exc
    return RespostaTransporteSefaz(extrair_ret_envi_nfe(payload),status)