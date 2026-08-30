from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from fiscal.choices_documento_fiscal import StatusDocumentoFiscal
from fiscal.models_documento_fiscal import DocumentoFiscal
from fiscal.services_assinatura_documento_fiscal import assinar_documento_fiscal


class AssinaturaDocumentoFiscalTests(TestCase):
    def _documento(self, *, status=StatusDocumentoFiscal.PREPARADO, xml="<NFe/>"):
        return DocumentoFiscal(
            venda_fiscal_id=1,
            matriz_id=1,
            loja_id=1,
            modelo="65",
            ambiente="homologacao",
            serie=1,
            numero=1,
            chave_acesso="1" * 44,
            codigo_numerico="12345678",
            digito_verificador="1",
            status=status,
            idempotency_key=f"195f3mb-{status}-{DocumentoFiscal.objects.count()}",
            xml_rascunho=xml,
        )

    @patch("fiscal.services_assinatura_documento_fiscal.transicionar_documento_fiscal")
    @patch("fiscal.services_assinatura_documento_fiscal.assinar_xml_nfe")
    @patch("fiscal.services_assinatura_documento_fiscal.carregar_certificado_a1")
    @patch("fiscal.services_assinatura_documento_fiscal.ConfiguracaoEmissaoFiscalLoja.objects.get")
    def test_assina_persiste_e_transiciona_para_pendente(
        self, get_config, carregar, assinar, transicionar
    ):
        documento=self._documento()
        documento.pk = 1
        documento._state.adding = False
        documento.save = Mock()
        lock_patch = patch(
            "fiscal.services_assinatura_documento_fiscal.DocumentoFiscal.objects.select_for_update"
        )
        lock = lock_patch.start()
        self.addCleanup(lock_patch.stop)
        lock.return_value.get.return_value = documento
        config=Mock(certificado_a1_referencia=r"C:\certificados\loja1.pfx")
        get_config.return_value=config
        cert=Mock()
        carregar.return_value=cert
        assinar.return_value="<NFe><Signature/></NFe>"

        retorno=assinar_documento_fiscal(
            documento=documento,
            senha_certificado="segredo",
        )

        carregar.assert_called_once_with(
            referencia=r"C:\certificados\loja1.pfx",
            senha="segredo",
        )
        assinar.assert_called_once_with(xml="<NFe/>", certificado_a1=cert)
        self.assertEqual(retorno.xml_assinado, "<NFe><Signature/></NFe>")
        documento.save.assert_called_once_with(
            update_fields=("xml_assinado", "atualizado_em")
        )
        transicionar.assert_called_once()
        self.assertEqual(
            transicionar.call_args.kwargs["novo_status"],
            StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
        )

    def test_rejeita_documento_fora_de_preparado(self):
        documento=self._documento(status=StatusDocumentoFiscal.RASCUNHO)
        lock_patch = patch(
            "fiscal.services_assinatura_documento_fiscal.DocumentoFiscal.objects.select_for_update"
        )
        lock = lock_patch.start()
        self.addCleanup(lock_patch.stop)
        lock.return_value.get.return_value = documento
        with self.assertRaises(ValidationError):
            assinar_documento_fiscal(
                documento=documento,
                senha_certificado="segredo",
            )

    def test_rejeita_xml_rascunho_ausente(self):
        documento=self._documento(xml="")
        lock_patch = patch(
            "fiscal.services_assinatura_documento_fiscal.DocumentoFiscal.objects.select_for_update"
        )
        lock = lock_patch.start()
        self.addCleanup(lock_patch.stop)
        lock.return_value.get.return_value = documento
        with self.assertRaises(ValidationError):
            assinar_documento_fiscal(
                documento=documento,
                senha_certificado="segredo",
            )

    @patch("fiscal.services_assinatura_documento_fiscal.ConfiguracaoEmissaoFiscalLoja.objects.get")
    def test_rejeita_referencia_a1_ausente(self, get_config):
        documento=self._documento()
        lock_patch = patch(
            "fiscal.services_assinatura_documento_fiscal.DocumentoFiscal.objects.select_for_update"
        )
        lock = lock_patch.start()
        self.addCleanup(lock_patch.stop)
        lock.return_value.get.return_value = documento
        get_config.return_value=Mock(certificado_a1_referencia="")
        with self.assertRaises(ValidationError):
            assinar_documento_fiscal(
                documento=documento,
                senha_certificado="segredo",
            )