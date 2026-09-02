from fiscal.services_autorizacao_documento_fiscal import reconciliar_retorno_consulta_protocolo
from fiscal.services_autorizacao_xml import AutorizacaoXMLNFCeError
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
                resolvedor_senha=lambda referencia: "senha-so-teste",
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
    def _retorno_consulta_protocolo(self, documento, cstat="100", motivo="Autorizado o uso da NF-e", chave=None, ambiente="2", data="2026-08-31T10:00:00-03:00", protocolo="135260000000001", versao_aplicacao="TESTE"):
        chave = documento.chave_acesso if chave is None else chave
        return (
            '<retConsSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            f'<tpAmb>{ambiente}</tpAmb><verAplic>{versao_aplicacao}</verAplic><cStat>{cstat}</cStat><xMotivo>{motivo}</xMotivo><chNFe>{chave}</chNFe>'
            '<protNFe versao="4.00"><infProt>'
            f'<tpAmb>{ambiente}</tpAmb><verAplic>{versao_aplicacao}</verAplic><chNFe>{chave}</chNFe><dhRecbto>{data}</dhRecbto><nProt>{protocolo}</nProt><cStat>{cstat}</cStat><xMotivo>{motivo}</xMotivo>'
            '</infProt></protNFe></retConsSitNFe>'
        )

    def _retorno_consulta_sem_protocolo(self, documento, cstat="217", motivo="NF-e nao consta"):
        return (
            '<retConsSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><tpAmb>2</tpAmb><verAplic>TESTE</verAplic>'
            f'<cStat>{cstat}</cStat><xMotivo>{motivo}</xMotivo><chNFe>{documento.chave_acesso}</chNFe></retConsSitNFe>'
        )

    def test_reconciliacao_consulta_autorizada(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        tentativa = documento.tentativa_atual
        documento = reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_protocolo(documento))
        self.assertEqual(documento.status, StatusDocumentoFiscal.AUTORIZADO)
        self.assertEqual(documento.codigo_status, "100")
        self.assertEqual(documento.protocolo_autorizacao, "135260000000001")
        self.assertIsNotNone(documento.data_autorizacao)
        self.assertIn("<nfeProc", documento.xml_autorizado)
        self.assertIn("<protNFe", documento.xml_autorizado)
        self.assertEqual(documento.tentativa_atual, tentativa)

    def test_reconciliacao_consulta_217_mantem_transmitindo(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        tentativa = documento.tentativa_atual
        reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_sem_protocolo(documento))
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.tentativa_atual, tentativa)
        self.assertEqual(documento.xml_autorizado, "")

    def test_reconciliacao_consulta_chave_divergente_rollback(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        tentativa = documento.tentativa_atual
        with self.assertRaisesMessage(ValidationError, "Chave consultada pela SEFAZ difere"):
            reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_protocolo(documento, chave="9" * 44))
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.tentativa_atual, tentativa)
        self.assertEqual(documento.xml_autorizado, "")

    def test_reconciliacao_consulta_ambiente_divergente_rollback(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        tentativa = documento.tentativa_atual
        with self.assertRaisesMessage(ValidationError, "Ambiente consultado na SEFAZ difere"):
            reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_protocolo(documento, ambiente="1"))
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.tentativa_atual, tentativa)
        self.assertEqual(documento.xml_autorizado, "")

    def test_reconciliacao_consulta_dhrecbto_invalido_rollback(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        tentativa = documento.tentativa_atual
        with self.assertRaisesMessage(ValidationError, "dhRecbto consultado"):
            reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_protocolo(documento, data="data-invalida"))
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.tentativa_atual, tentativa)
        self.assertEqual(documento.xml_autorizado, "")

    def test_reconciliacao_consulta_protocolo_incompleto_nao_autoriza(self):
        documento = iniciar_transmissao_documento_fiscal(documento=self._documento_assinado())
        tentativa = documento.tentativa_atual
        with self.assertRaisesMessage(AutorizacaoXMLNFCeError, "Consulta autorizada incompleta"):
            reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_protocolo(documento, protocolo=""))
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.TRANSMITINDO)
        self.assertEqual(documento.tentativa_atual, tentativa)
        self.assertEqual(documento.xml_autorizado, "")

    def test_reconciliacao_consulta_exige_transmitindo(self):
        documento = self._documento_assinado()
        with self.assertRaisesMessage(ValidationError, "Reconciliacao exige documento em transmissao"):
            reconciliar_retorno_consulta_protocolo(documento=documento, xml_retorno=self._retorno_consulta_sem_protocolo(documento))
        documento.refresh_from_db()
        self.assertEqual(documento.status, StatusDocumentoFiscal.PENDENTE_TRANSMISSAO)
