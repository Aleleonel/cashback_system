from decimal import Decimal

from django.test import SimpleTestCase

from fiscal.dto_documento_fiscal import (
    DadosDestinatarioDocumentoFiscal,
    DadosDocumentoFiscal,
    DadosEmitenteDocumentoFiscal,
    DadosItemDocumentoFiscal,
    DadosPagamentoDocumentoFiscal,
)


class ContratoDadosNFCeTests(SimpleTestCase):
    def test_dtos_novos_existem(self):
        pagamento = DadosPagamentoDocumentoFiscal(
            codigo="PIX",
            tipo="pix",
            descricao="PIX",
            valor=Decimal("10.00"),
        )
        destinatario = DadosDestinatarioDocumentoFiscal(
            cpf_cnpj="12345678901",
            nome="Cliente",
        )
        emitente = DadosEmitenteDocumentoFiscal(
            cnpj="12345678000199",
            razao_social="Loja Fiscal Ltda",
            nome_fantasia="Loja Fiscal",
            inscricao_estadual="123456789",
            crt="3",
            logradouro="Rua Teste",
            numero="100",
            complemento="",
            bairro="Centro",
            codigo_municipio_ibge="3550308",
            municipio="Sao Paulo",
            uf="SP",
            cep="01001000",
        )
        self.assertEqual(pagamento.tipo, "pix")
        self.assertEqual(destinatario.cpf_cnpj, "12345678901")
        self.assertEqual(emitente.codigo_municipio_ibge, "3550308")

    def test_campos_comerciais_do_item_tem_defaults(self):
        campos = DadosItemDocumentoFiscal.__dataclass_fields__
        for nome in ("codigo_produto", "descricao_produto", "unidade_comercial", "gtin"):
            self.assertIn(nome, campos)

    def test_documento_tem_emitente_destinatario_e_pagamentos(self):
        campos = DadosDocumentoFiscal.__dataclass_fields__
        self.assertIn("emitente", campos)
        self.assertIn("destinatario", campos)
        self.assertIn("pagamentos", campos)
