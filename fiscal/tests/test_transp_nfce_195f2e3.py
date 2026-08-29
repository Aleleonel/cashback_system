from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.tests.test_services_xml_nfce_195f1c import dados, gerar


NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


class TransporteNFCe195F2E3Tests(SimpleTestCase):
    def test_transp_modfrete_9_e_serializado(self):
        root = ET.fromstring(gerar(dados()))
        transp = root.find("nfe:infNFe/nfe:transp", NS)

        self.assertIsNotNone(transp)
        self.assertEqual(
            transp.findtext("nfe:modFrete", namespaces=NS),
            "9",
        )

    def test_transp_fica_entre_total_e_pag(self):
        root = ET.fromstring(gerar(dados()))
        inf_nfe = root.find("nfe:infNFe", NS)
        nomes = [elemento.tag.rsplit("}", 1)[-1] for elemento in list(inf_nfe)]

        self.assertLess(nomes.index("total"), nomes.index("transp"))
        self.assertLess(nomes.index("transp"), nomes.index("pag"))

    def test_sem_grupos_de_transportador(self):
        root = ET.fromstring(gerar(dados()))
        transp = root.find("nfe:infNFe/nfe:transp", NS)

        self.assertIsNone(transp.find("nfe:transporta", NS))
        self.assertIsNone(transp.find("nfe:veicTransp", NS))
        self.assertIsNone(transp.find("nfe:reboque", NS))
        self.assertIsNone(transp.find("nfe:vol", NS))