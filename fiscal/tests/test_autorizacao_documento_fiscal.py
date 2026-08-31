from django.core.exceptions import ValidationError
from unittest.mock import patch

from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from fiscal.services_assinatura_documento_fiscal import assinar_documento_fiscal
from fiscal.services_autorizacao_documento_fiscal import (
    iniciar_transmissao_documento_fiscal,
    preparar_lote_autorizacao,
    registrar_retorno_autorizacao,
)
from fiscal.services_geracao_xml_documento_fiscal import (
    gerar_e_persistir_xml_rascunho_nfce,
)
from fiscal.services_preparacao_documento_fiscal import preparar_documento_fiscal
from fiscal.tests.test_integracao_persistencia_xml_nfce import (
    IntegracaoPersistenciaXMLNFCeTests,
)


NS = "http://www.portalfiscal.inf.br/nfe"


class AutorizacaoDocumentoFiscalTests(IntegracaoPersistenciaXMLNFCeTests):
    def _documento_assinado(self):
        config = ConfiguracaoEmissaoFiscalLoja.objects.get(loja=self.loja)
        config.certificado_a1_referencia = "certificados/teste.pfx"
        config.save(
            update_fields=(
                "certificado_a1_referencia",
                "atualizado_em",
            )
        )

        with patch(
            "fiscal.services_chave_acesso.secrets.randbelow",
            return_value=12345678,
        ):
            documento, _, _ = preparar_documento_fiscal(
                venda_fiscal=self.venda_fiscal,
                modelo=ModeloDocumentoFiscal.NFCE,
                ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
                serie=1,
            )
            documento = gerar_e_persistir_xml_rascunho_nfce(
                documento=documento
            )

        with patch(
            "fiscal.services_assinatura_documento_fiscal.carregar_certificado_a1",
            return_value=object(),
        ), patch(
            "fiscal.services_assinatura_documento_fiscal.assinar_xml_nfe",
            side_effect=lambda **kwargs: kwargs["xml"],
        ):
            documento = assinar_documento_fiscal(
                documento=documento,
                senha_certificado="senha-so-teste",
            )

        documento.refresh_from_db()
        return documento

    def _retorno(
        self,
        documento,
        cstat="100",
        motivo="Autorizado",
        protocolo="135260000000001",
    ):
        return (
            f'<retEnviNFe xmlns="{NS}" versao="4.00">'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            '<cStat>104</cStat><xMotivo>Lote processado</xMotivo>'
            '<protNFe versao="4.00"><infProt>'
            '<tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            f'<chNFe>{documento.chave_acesso}</chNFe>'
            '<dhRecbto>2026-08-30T10:00:00-03:00</dhRecbto>'
            f'<nProt>{protocolo}</nProt><digVal>ABC=</digVal>'
            f'<cStat>{cstat}</cStat><xMotivo>{motivo}</xMotivo>'
            '</infProt></protNFe></retEnviNFe>'
        )

    def test_inicia_transmissao_incrementa_tentativa(self):
        documento = self._documento_assinado()
        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
        )

        documento = iniciar_transmissao_documento_fiscal(
            documento=documento
        )

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.TRANSMITINDO,
        )
        self.assertEqual(documento.tentativa_atual, 1)
        self.assertIsNotNone(documento.ultima_tentativa_em)

    def test_prepara_lote_sincrono_sem_rede(self):
        documento = iniciar_transmissao_documento_fiscal(
            documento=self._documento_assinado()
        )
        lote = preparar_lote_autorizacao(documento=documento)

        self.assertIn("<enviNFe", lote)
        self.assertIn("<indSinc>1</indSinc>", lote)
        self.assertIn("<NFe", lote)

    def test_registra_autorizacao_e_nfeproc(self):
        documento = iniciar_transmissao_documento_fiscal(
            documento=self._documento_assinado()
        )
        documento = registrar_retorno_autorizacao(
            documento=documento,
            xml_retorno=self._retorno(documento),
        )

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.AUTORIZADO,
        )
        self.assertEqual(documento.codigo_status, "100")
        self.assertEqual(
            documento.protocolo_autorizacao,
            "135260000000001",
        )
        self.assertIn("<nfeProc", documento.xml_autorizado)
        self.assertIn("<protNFe", documento.xml_autorizado)
        self.assertTrue(documento.xml_retorno)

    def test_registra_rejeicao(self):
        documento = iniciar_transmissao_documento_fiscal(
            documento=self._documento_assinado()
        )
        documento = registrar_retorno_autorizacao(
            documento=documento,
            xml_retorno=self._retorno(
                documento,
                cstat="539",
                motivo="Duplicidade",
                protocolo="",
            ),
        )

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.REJEITADO,
        )
        self.assertEqual(documento.codigo_status, "539")
        self.assertEqual(documento.motivo_status, "Duplicidade")
        self.assertEqual(documento.xml_autorizado, "")

    def test_204_permanece_rejeitado_sem_reconciliacao(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        documento = registrar_retorno_autorizacao(documento=documento, xml_retorno=self._retorno(documento, cstat="204", motivo="Duplicidade de NF-e", protocolo=""))
        self.assertEqual(documento.status, StatusDocumentoFiscal.REJEITADO)
        self.assertEqual(documento.codigo_status, "204")
        self.assertEqual(documento.xml_autorizado, "")

    def test_bloqueia_dhrecbto_invalido_sem_autorizar(self):
        documento = iniciar_transmissao_documento_fiscal(
            documento=self._documento_assinado()
        )
        retorno = self._retorno(documento).replace("2026-08-30T10:00:00-03:00", "data-invalida")
        with self.assertRaisesMessage(ValidationError, "dhRecbto"):
            registrar_retorno_autorizacao(documento=documento, xml_retorno=retorno)
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.xml_autorizado, "")

    def test_bloqueia_ambiente_divergente_sem_autorizar(self):
        documento = iniciar_transmissao_documento_fiscal(
            documento=self._documento_assinado()
        )
        retorno = self._retorno(documento).replace(
            "<protNFe versao=\"4.00\"><infProt><tpAmb>2</tpAmb>",
            "<protNFe versao=\"4.00\"><infProt><tpAmb>1</tpAmb>",
        )
        with self.assertRaisesMessage(ValidationError, "Ambiente retornado"):
            registrar_retorno_autorizacao(documento=documento, xml_retorno=retorno)
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.xml_autorizado, "")

    def test_bloqueia_chave_divergente(self):
        documento = iniciar_transmissao_documento_fiscal(
            documento=self._documento_assinado()
        )
        retorno = self._retorno(documento).replace(
            documento.chave_acesso,
            "9" * 44,
        )

        with self.assertRaisesMessage(Exception, "Chave retornada"):
            registrar_retorno_autorizacao(
                documento=documento,
                xml_retorno=retorno,
            )