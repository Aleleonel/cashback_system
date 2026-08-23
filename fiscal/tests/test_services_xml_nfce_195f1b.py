from datetime import datetime, timezone
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from django.test import SimpleTestCase

from fiscal.services_xml_nfce import (
    NFE_NAMESPACE,
    NFCeXMLError,
    gerar_xml_nfce_195f1b,
)


NS = {"nfe": NFE_NAMESPACE}


def _emitente():
    return SimpleNamespace(
        cnpj="12345678000195",
        razao_social="Loja Fiscal Ltda",
        nome_fantasia="Loja Fiscal",
        inscricao_estadual="123456789",
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        codigo_municipio_ibge="3550308",
        municipio="Sao Paulo",
        uf="SP",
        cep="01001000",
    )


def _destinatario():
    return SimpleNamespace(
        cpf_cnpj="12345678901",
        nome="Cliente Teste",
        email="cliente@example.com",
    )


def _documento():
    return SimpleNamespace(
        chave_acesso="35260812345678000195650010000000011123456780",
        modelo="65",
        ambiente="homologacao",
        serie=1,
        numero=1,
    )


def _dados(destinatario=True):
    return SimpleNamespace(
        emitente=_emitente(),
        destinatario=_destinatario() if destinatario else None,
    )


class NFCeXML195F1BTests(SimpleTestCase):

    def gerar(self, *, dados=None, documento=None, data_emissao=None):
        return gerar_xml_nfce_195f1b(
            documento=documento or _documento(),
            dados=dados or _dados(),
            data_emissao=data_emissao or datetime(
                2026, 8, 22, 13, 30, 0, tzinfo=timezone.utc
            ),
            crt="1",
            natureza_operacao="VENDA",
            versao_processo="ProCash-195F1B",
        )

    def test_ide_possui_campos_basicos_nfce(self):
        root = ET.fromstring(self.gerar())
        ide = root.find("nfe:infNFe/nfe:ide", NS)

        self.assertIsNotNone(ide)
        self.assertEqual(ide.findtext("nfe:cUF", namespaces=NS), "35")
        self.assertEqual(ide.findtext("nfe:mod", namespaces=NS), "65")
        self.assertEqual(ide.findtext("nfe:serie", namespaces=NS), "1")
        self.assertEqual(ide.findtext("nfe:nNF", namespaces=NS), "1")
        self.assertEqual(ide.findtext("nfe:cMunFG", namespaces=NS), "3550308")
        self.assertEqual(ide.findtext("nfe:tpAmb", namespaces=NS), "2")

    def test_ide_deriva_cnf_e_cdv_da_chave(self):
        root = ET.fromstring(self.gerar())
        ide = root.find("nfe:infNFe/nfe:ide", NS)

        self.assertEqual(
            ide.findtext("nfe:cNF", namespaces=NS),
            _documento().chave_acesso[35:43],
        )
        self.assertEqual(
            ide.findtext("nfe:cDV", namespaces=NS),
            _documento().chave_acesso[-1],
        )

    def test_dhemi_contem_timezone(self):
        root = ET.fromstring(self.gerar())
        ide = root.find("nfe:infNFe/nfe:ide", NS)

        dh_emi = ide.findtext("nfe:dhEmi", namespaces=NS)

        self.assertEqual(dh_emi, "2026-08-22T13:30:00+00:00")

    def test_emitente_e_endereco_sao_gerados(self):
        root = ET.fromstring(self.gerar())
        emit = root.find("nfe:infNFe/nfe:emit", NS)

        self.assertEqual(
            emit.findtext("nfe:CNPJ", namespaces=NS),
            "12345678000195",
        )
        self.assertEqual(
            emit.findtext("nfe:xNome", namespaces=NS),
            "Loja Fiscal Ltda",
        )
        self.assertEqual(
            emit.findtext("nfe:IE", namespaces=NS),
            "123456789",
        )
        self.assertEqual(
            emit.findtext("nfe:CRT", namespaces=NS),
            "1",
        )

        endereco = emit.find("nfe:enderEmit", NS)
        self.assertEqual(
            endereco.findtext("nfe:cMun", namespaces=NS),
            "3550308",
        )
        self.assertEqual(
            endereco.findtext("nfe:UF", namespaces=NS),
            "SP",
        )
        self.assertEqual(
            endereco.findtext("nfe:CEP", namespaces=NS),
            "01001000",
        )

    def test_destinatario_cpf_e_email_sao_gerados(self):
        root = ET.fromstring(self.gerar())
        dest = root.find("nfe:infNFe/nfe:dest", NS)

        self.assertIsNotNone(dest)
        self.assertEqual(
            dest.findtext("nfe:CPF", namespaces=NS),
            "12345678901",
        )
        self.assertEqual(
            dest.findtext("nfe:xNome", namespaces=NS),
            "Cliente Teste",
        )
        self.assertEqual(
            dest.findtext("nfe:email", namespaces=NS),
            "cliente@example.com",
        )

    def test_destinatario_ausente_nao_cria_tag_dest(self):
        root = ET.fromstring(self.gerar(dados=_dados(destinatario=False)))

        dest = root.find("nfe:infNFe/nfe:dest", NS)

        self.assertIsNone(dest)

    def test_rejeita_data_emissao_sem_timezone(self):
        with self.assertRaises(NFCeXMLError):
            self.gerar(
                data_emissao=datetime(2026, 8, 22, 13, 30, 0)
            )

    def test_rejeita_modelo_diferente_de_65(self):
        documento = _documento()
        documento.modelo = "55"

        with self.assertRaises(NFCeXMLError):
            self.gerar(documento=documento)
