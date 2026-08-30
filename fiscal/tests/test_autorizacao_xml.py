from django.test import SimpleTestCase
from lxml import etree

from fiscal.services_autorizacao_xml import (
    AutorizacaoXMLNFCeError,
    interpretar_ret_envi_nfe,
    montar_envi_nfe,
    montar_nfe_proc,
)


NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
CHAVE = "35260812345678000199650010000000011000000010"


class AutorizacaoXMLNFCeTests(SimpleTestCase):
    def xml_nfe(self):
        return (
            '<NFe xmlns="http://www.portalfiscal.inf.br/nfe">'
            f'<infNFe Id="NFe{CHAVE}" versao="4.00"/>'
            "</NFe>"
        )

    def test_monta_envi_nfe_sincrono(self):
        xml = montar_envi_nfe(xml_assinado=self.xml_nfe(), id_lote="1", ind_sinc=1)
        raiz = etree.fromstring(xml.encode())
        self.assertEqual(raiz.tag, "{http://www.portalfiscal.inf.br/nfe}enviNFe")
        self.assertEqual(raiz.get("versao"), "4.00")
        self.assertEqual(raiz.findtext("nfe:idLote", namespaces=NS), "1")
        self.assertEqual(raiz.findtext("nfe:indSinc", namespaces=NS), "1")
        self.assertIsNotNone(raiz.find("nfe:NFe", namespaces=NS))

    def test_rejeita_id_lote_invalido(self):
        with self.assertRaises(AutorizacaoXMLNFCeError):
            montar_envi_nfe(xml_assinado=self.xml_nfe(), id_lote="ABC")

    def test_interpreta_retorno_autorizado_pelo_infprot(self):
        retorno = interpretar_ret_envi_nfe(xml_retorno=(
            '<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic><cStat>104</cStat>'
            '<xMotivo>Lote processado</xMotivo>'
            '<protNFe versao="4.00"><infProt>'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            f'<chNFe>{CHAVE}</chNFe><dhRecbto>2026-08-30T10:00:00-03:00</dhRecbto>'
            '<nProt>135260000000001</nProt><digVal>ABC=</digVal>'
            '<cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo>'
            '</infProt></protNFe></retEnviNFe>'
        ))
        self.assertTrue(retorno.autorizado)
        self.assertEqual(retorno.codigo_status, "100")
        self.assertEqual(retorno.protocolo, "135260000000001")
        self.assertEqual(retorno.chave_acesso, CHAVE)
        self.assertIn("<protNFe", retorno.xml_protocolo)

    def test_interpreta_rejeicao_do_protocolo(self):
        retorno = interpretar_ret_envi_nfe(xml_retorno=(
            '<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<cStat>104</cStat><xMotivo>Lote processado</xMotivo>'
            '<protNFe versao="4.00"><infProt>'
            f'<chNFe>{CHAVE}</chNFe><cStat>539</cStat>'
            '<xMotivo>Duplicidade de NF-e</xMotivo>'
            '</infProt></protNFe></retEnviNFe>'
        ))
        self.assertFalse(retorno.autorizado)
        self.assertEqual(retorno.codigo_status, "539")
        self.assertEqual(retorno.motivo_status, "Duplicidade de NF-e")

    def test_preserva_recibo_quando_retorno_assincrono(self):
        retorno = interpretar_ret_envi_nfe(xml_retorno=(
            '<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<cStat>103</cStat><xMotivo>Lote recebido com sucesso</xMotivo>'
            '<infRec><nRec>351000000000001</nRec><tMed>1</tMed></infRec>'
            '</retEnviNFe>'
        ))
        self.assertEqual(retorno.codigo_status, "103")
        self.assertEqual(retorno.numero_recibo, "351000000000001")

    def test_autorizado_exige_chave_protocolo_e_data(self):
        casos = (("chNFe", "<dhRecbto>2026-08-30T10:00:00-03:00</dhRecbto><nProt>135260000000001</nProt>"), ("dhRecbto", f"<chNFe>{CHAVE}</chNFe><nProt>135260000000001</nProt>"), ("nProt", f"<chNFe>{CHAVE}</chNFe><dhRecbto>2026-08-30T10:00:00-03:00</dhRecbto>"))
        for campo, conteudo in casos:
            with self.subTest(campo=campo):
                xml = ('<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><cStat>104</cStat><xMotivo>Lote processado</xMotivo><protNFe versao="4.00"><infProt>' + conteudo + '<cStat>100</cStat><xMotivo>Autorizado</xMotivo></infProt></protNFe></retEnviNFe>')
                with self.assertRaisesMessage(AutorizacaoXMLNFCeError, "Retorno autorizado incompleto"):
                    interpretar_ret_envi_nfe(xml_retorno=xml)

    def test_204_e_539_permanecem_nao_autorizados(self):
        for cstat in ("204", "539"):
            with self.subTest(cstat=cstat):
                retorno = interpretar_ret_envi_nfe(xml_retorno=('<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><cStat>104</cStat><xMotivo>Lote processado</xMotivo><protNFe versao="4.00"><infProt>' + f'<chNFe>{CHAVE}</chNFe><cStat>{cstat}</cStat><xMotivo>Rejeicao de duplicidade</xMotivo></infProt></protNFe></retEnviNFe>'))
                self.assertFalse(retorno.autorizado)
                self.assertEqual(retorno.codigo_status, cstat)

    def test_nfe_proc_rejeita_chave_divergente(self):
        protocolo = '<protNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><infProt>' + f'<chNFe>{"9" * 44}</chNFe><nProt>135260000000001</nProt><cStat>100</cStat><xMotivo>Autorizado</xMotivo></infProt></protNFe>'
        with self.assertRaisesMessage(AutorizacaoXMLNFCeError, "Chave do protocolo difere"):
            montar_nfe_proc(xml_assinado=self.xml_nfe(), xml_protocolo=protocolo)

    def test_nfe_proc_rejeita_protocolo_nao_autorizado(self):
        protocolo = '<protNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><infProt>' + f'<chNFe>{CHAVE}</chNFe><nProt>135260000000001</nProt><cStat>539</cStat><xMotivo>Duplicidade</xMotivo></infProt></protNFe>'
        with self.assertRaisesMessage(AutorizacaoXMLNFCeError, "cStat 100"):
            montar_nfe_proc(xml_assinado=self.xml_nfe(), xml_protocolo=protocolo)

    def test_monta_nfe_proc_com_nfe_e_protocolo(self):
        retorno = interpretar_ret_envi_nfe(xml_retorno=(
            '<retEnviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<cStat>104</cStat><xMotivo>Lote processado</xMotivo>'
            '<protNFe versao="4.00"><infProt>'
            f'<chNFe>{CHAVE}</chNFe>'
            '<dhRecbto>2026-08-30T10:00:00-03:00</dhRecbto>'
            '<nProt>135260000000001</nProt>'
            '<cStat>100</cStat><xMotivo>Autorizado</xMotivo>'
            '</infProt></protNFe></retEnviNFe>'
        ))
        proc = montar_nfe_proc(xml_assinado=self.xml_nfe(), xml_protocolo=retorno.xml_protocolo)
        raiz = etree.fromstring(proc.encode())
        self.assertEqual(raiz.tag, "{http://www.portalfiscal.inf.br/nfe}nfeProc")
        self.assertEqual(raiz.get("versao"), "4.00")
        self.assertIsNotNone(raiz.find("nfe:NFe", namespaces=NS))
        self.assertIsNotNone(raiz.find("nfe:protNFe", namespaces=NS))