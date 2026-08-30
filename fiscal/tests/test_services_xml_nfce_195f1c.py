from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import NFE_NAMESPACE, NFCeXMLError, gerar_xml_nfce_195f1c

NS = {"nfe": NFE_NAMESPACE}

def emitente():
    return SimpleNamespace(cnpj="12345678000195", razao_social="Loja Fiscal Ltda",
        nome_fantasia="Loja Fiscal", inscricao_estadual="123456789",
        logradouro="Rua Teste", numero="100", bairro="Centro",
        codigo_municipio_ibge="3550308", municipio="Sao Paulo", uf="SP", cep="01001000")

def documento():
    return SimpleNamespace(chave_acesso="35260812345678000195650010000000011123456780",
        modelo="65", ambiente="homologacao", serie=1, numero=1)

def item(**extra):
    d=dict(codigo="SKU-1", descricao="Produto Teste", ncm_codigo="21069090",
        cest_codigo="", cfop_codigo="5102", unidade_comercial="UN", gtin="",
        quantidade=Decimal("2.0000"), valor_unitario=Decimal("10.00"),
        valor_produtos=Decimal("20.00"), desconto=Decimal("2.00"),
        frete=Decimal("1.00"), seguro=Decimal("0.00"),
        outras_despesas=Decimal("0.50"))
    d.update(extra); return SimpleNamespace(**d)

def pagamento(tipo="pix", valor="19.50", troco="0.00"):
    return SimpleNamespace(codigo=tipo.upper(), tipo=tipo,
        descricao=tipo, valor=Decimal(valor), troco=Decimal(troco))

def dados(itens=None, pagamentos=None):
    return SimpleNamespace(emitente=emitente(), destinatario=None,
        uf_origem="SP",
        itens=tuple(itens if itens is not None else [item()]),
        pagamentos=tuple(pagamentos if pagamentos is not None else [pagamento()]))

def gerar(d=None):
    return gerar_xml_nfce_195f1c(documento=documento(), dados=d or dados(),
        data_emissao=datetime(2026,8,22,14,0,0,tzinfo=timezone.utc),
        crt="1", versao_processo="ProCash-195F1C")

class NFCeXML195F1CTests(SimpleTestCase):
    def test_cria_det_com_nitem_sequencial(self):
        root=ET.fromstring(gerar(dados(itens=[item(), item(codigo="SKU-2")])))
        det=root.findall("nfe:infNFe/nfe:det",NS)
        self.assertEqual([x.attrib["nItem"] for x in det],["1","2"])

    def test_produto_contem_campos_comerciais(self):
        root=ET.fromstring(gerar())
        prod=root.find("nfe:infNFe/nfe:det/nfe:prod",NS)
        self.assertEqual(prod.findtext("nfe:cProd",namespaces=NS),"SKU-1")
        self.assertEqual(prod.findtext("nfe:cEAN",namespaces=NS),"SEM GTIN")
        self.assertEqual(prod.findtext("nfe:NCM",namespaces=NS),"21069090")
        self.assertEqual(prod.findtext("nfe:CFOP",namespaces=NS),"5102")
        self.assertEqual(prod.findtext("nfe:qCom",namespaces=NS),"2.0000")
        self.assertEqual(prod.findtext("nfe:vProd",namespaces=NS),"20.00")
        self.assertEqual(prod.findtext("nfe:vDesc",namespaces=NS),"2.00")

    def test_total_icmstot_comercial(self):
        root=ET.fromstring(gerar())
        tot=root.find("nfe:infNFe/nfe:total/nfe:ICMSTot",NS)
        self.assertEqual(tot.findtext("nfe:vProd",namespaces=NS),"20.00")
        self.assertEqual(tot.findtext("nfe:vFrete",namespaces=NS),"1.00")
        self.assertEqual(tot.findtext("nfe:vDesc",namespaces=NS),"2.00")
        self.assertEqual(tot.findtext("nfe:vOutro",namespaces=NS),"0.50")
        self.assertEqual(tot.findtext("nfe:vNF",namespaces=NS),"19.50")

    def test_pagamento_pix_mapeia_17(self):
        root=ET.fromstring(gerar())
        dp=root.find("nfe:infNFe/nfe:pag/nfe:detPag",NS)
        self.assertEqual(dp.findtext("nfe:tPag",namespaces=NS),"17")
        self.assertEqual(dp.findtext("nfe:vPag",namespaces=NS),"19.50")

    def test_pagamentos_basicos_mapeiam_codigos_nfce(self):
        ps=[pagamento("dinheiro","5"), pagamento("cartao_credito","5"),
            pagamento("cartao_debito","5"), pagamento("pix","4.50")]
        root=ET.fromstring(gerar(dados(pagamentos=ps)))
        cod=[x.findtext("nfe:tPag",namespaces=NS)
             for x in root.findall("nfe:infNFe/nfe:pag/nfe:detPag",NS)]
        self.assertEqual(cod,["01","03","04","17"])

    def test_troco_gera_vtroco(self):
        root=ET.fromstring(gerar(dados(pagamentos=[pagamento("dinheiro","20","0.50")])))
        self.assertEqual(root.findtext("nfe:infNFe/nfe:pag/nfe:vTroco",namespaces=NS),"0.50")

    def test_sem_itens_rejeita(self):
        with self.assertRaises(NFCeXMLError): gerar(dados(itens=[]))

    def test_sem_pagamentos_rejeita(self):
        with self.assertRaises(NFCeXMLError): gerar(dados(pagamentos=[]))

    def test_ncm_invalido_rejeita(self):
        with self.assertRaises(NFCeXMLError): gerar(dados(itens=[item(ncm_codigo="2106")]))

    def test_grupo_imposto_reservado_existe_sem_tributos(self):
        root=ET.fromstring(gerar())
        imposto=root.find("nfe:infNFe/nfe:det/nfe:imposto",NS)
        self.assertIsNotNone(imposto)
        self.assertEqual(len(imposto),0)
