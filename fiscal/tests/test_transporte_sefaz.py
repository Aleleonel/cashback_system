import io
import socket
import ssl
import urllib.error
from pathlib import Path
from datetime import datetime,timedelta,timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase
from lxml import etree
from fiscal.services_transporte_sefaz import *
from fiscal.services_transporte_sefaz import _ssl_contexto_a1

class A1:
    def __init__(self):
        self.chave_privada=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        n=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,"TESTE")]);now=datetime.now(timezone.utc)
        self.certificado=(x509.CertificateBuilder().subject_name(n).issuer_name(n).public_key(self.chave_privada.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=1)).sign(self.chave_privada,hashes.SHA256()))
class Resp:
    status=200
    def __init__(self,data):self.data=data
    def read(self):return self.data
    def __enter__(self):return self
    def __exit__(self,*args):return False
class TransporteSefazTests(SimpleTestCase):
    ENVI='<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>1</idLote><indSinc>1</indSinc><NFe/></enviNFe>'
    RET='<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><tpAmb>2</tpAmb><cStat>100</cStat><xMotivo>OK</xMotivo></retEnviNFe>'
    def soap(self):return ('<s:Envelope xmlns:s="'+SOAP12_NS+'"><s:Body>'+self.RET+'</s:Body></s:Envelope>').encode()
    def test_endpoints(self):
        self.assertIn("homologacao.nfce",endpoint_autorizacao_nfce_sp("homologacao"));self.assertIn("nfce.fazenda.sp.gov.br/ws",endpoint_autorizacao_nfce_sp("producao"))
        with self.assertRaises(TransporteSefazError):endpoint_autorizacao_nfce_sp("x")
    def test_envelope(self):
        r=etree.fromstring(montar_envelope_soap12_autorizacao(self.ENVI));self.assertEqual(SOAP12_NS,etree.QName(r).namespace);self.assertEqual(1,len(r.xpath("//*[local-name()='nfeDadosMsg']")))
    def test_extracao(self):self.assertIn("<cStat>100</cStat>",extrair_ret_envi_nfe(self.soap()))
    def test_fault(self):
        x=b'<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><s:Fault><s:Reason><s:Text>Falha teste</s:Text></s:Reason></s:Fault></s:Body></s:Envelope>'
        with self.assertRaisesRegex(TransporteSefazError,"Falha teste"):extrair_ret_envi_nfe(x)
    def test_mock(self):
        cap={}
        def op(req,context=None,timeout=None):cap["req"]=req;cap["timeout"]=timeout;return Resp(self.soap())
        r=transmitir_autorizacao_nfce_sp(xml_envi_nfe=self.ENVI,ambiente="homologacao",certificado_a1=A1(),timeout=7,opener=op)
        self.assertEqual(200,r.http_status);self.assertEqual("POST",cap["req"].get_method());self.assertEqual(7,cap["timeout"]);self.assertIn(SOAP_ACTION,cap["req"].get_header("Content-type"))
    def test_http_error(self):
        def op(*a,**k):raise urllib.error.HTTPError("https://teste",500,"erro",{},io.BytesIO())
        with self.assertRaisesRegex(TransporteSefazError,"500"):transmitir_autorizacao_nfce_sp(xml_envi_nfe=self.ENVI,ambiente="homologacao",certificado_a1=A1(),opener=op)
    def test_http_error_com_ret_envi_nfe_preserva_retorno(self):
        payload = self.soap()

        def op(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://teste",
                500,
                "erro",
                {},
                io.BytesIO(payload),
            )

        resposta = transmitir_autorizacao_nfce_sp(
            xml_envi_nfe=self.ENVI,
            ambiente="homologacao",
            certificado_a1=A1(),
            opener=op,
        )
        self.assertEqual(500, resposta.http_status)
        self.assertIn("<retEnviNFe", resposta.xml_retorno)

    def test_cadeia_adicional_a1_e_incluida_no_pem_cliente(self):
        from unittest.mock import patch

        a1 = A1()
        a1.certificados_adicionais = (a1.certificado,)
        capturado = {}

        def fake_load_cert_chain(contexto, certfile, keyfile, *args, **kwargs):
            capturado["cert_pem"] = Path(certfile).read_bytes()

        with patch(
            "ssl.SSLContext.load_cert_chain",
            new=fake_load_cert_chain,
        ):
            _ssl_contexto_a1(a1)

        self.assertEqual(
            2,
            capturado["cert_pem"].count(b"-----BEGIN CERTIFICATE-----"),
        )

    def test_timeout(self):
        def op(*a,**k):raise socket.timeout()
        with self.assertRaisesRegex(TransporteSefazError,"comunicacao"):transmitir_autorizacao_nfce_sp(xml_envi_nfe=self.ENVI,ambiente="homologacao",certificado_a1=A1(),opener=op)
    def test_resposta_xml_invalida(self):
        with self.assertRaisesRegex(TransporteSefazError,"XML invalida"):
            extrair_ret_envi_nfe(b"<nao-fechado>")

    def test_resposta_sem_ret_envi_nfe(self):
        xml=b'<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><outraResposta/></s:Body></s:Envelope>'
        with self.assertRaisesRegex(TransporteSefazError,"sem retEnviNFe unico"):
            extrair_ret_envi_nfe(xml)

    def test_resposta_com_dois_ret_envi_nfe(self):
        xml=('<s:Envelope xmlns:s="'+SOAP12_NS+'"><s:Body>'+self.RET+self.RET+'</s:Body></s:Envelope>').encode()
        with self.assertRaisesRegex(TransporteSefazError,"sem retEnviNFe unico"):
            extrair_ret_envi_nfe(xml)

    def test_pems_temporarios_removidos_se_load_cert_chain_falhar(self):
        import glob
        import tempfile
        from unittest.mock import patch
        antes=set(glob.glob(tempfile.gettempdir()+"/nfce_tls_*"))
        with patch("ssl.SSLContext.load_cert_chain",side_effect=ssl.SSLError("falha sintetica")):
            with self.assertRaises(ssl.SSLError):
                transmitir_autorizacao_nfce_sp(
                    xml_envi_nfe=self.ENVI,ambiente="homologacao",
                    certificado_a1=A1(),opener=lambda *a,**k: None,
                )
        depois=set(glob.glob(tempfile.gettempdir()+"/nfce_tls_*"))
        self.assertEqual(antes,depois)