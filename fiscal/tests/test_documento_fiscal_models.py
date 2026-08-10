from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from fiscal.choices_documento_fiscal import (
    AmbienteDocumentoFiscal,
    ModeloDocumentoFiscal,
    StatusDocumentoFiscal,
)
from fiscal.models_documento_fiscal import (
    DocumentoFiscal,
    SequenciaDocumentoFiscal,
)


class DocumentoFiscalModelTests(SimpleTestCase):
    def documento(self, **overrides):
        dados = {
            "venda_fiscal_id": 1,
            "matriz_id": 1,
            "loja_id": 1,
            "modelo": ModeloDocumentoFiscal.NFCE,
            "ambiente": AmbienteDocumentoFiscal.HOMOLOGACAO,
            "serie": 1,
            "idempotency_key": "teste-188",
        }
        dados.update(overrides)
        return DocumentoFiscal(**dados)

    def test_defaults(self):
        documento = self.documento()

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.RASCUNHO,
        )
        self.assertIsNone(documento.numero)
        self.assertEqual(documento.tentativa_atual, 0)

    def test_aceita_chave_44_digitos(self):
        documento = self.documento(
            chave_acesso="1" * 44,
        )

        documento.clean()

        self.assertEqual(
            documento.chave_acesso,
            "1" * 44,
        )

    def test_rejeita_chave_invalida(self):
        documento = self.documento(
            chave_acesso="ABC",
        )

        with self.assertRaises(ValidationError) as erro:
            documento.clean()

        self.assertIn(
            "chave_acesso",
            erro.exception.message_dict,
        )

    def test_rejeita_serie_zero(self):
        documento = self.documento(
            serie=0,
        )

        with self.assertRaises(ValidationError) as erro:
            documento.clean()

        self.assertIn(
            "serie",
            erro.exception.message_dict,
        )

    def test_rejeita_numero_zero(self):
        documento = self.documento(
            numero=0,
        )

        with self.assertRaises(ValidationError) as erro:
            documento.clean()

        self.assertIn(
            "numero",
            erro.exception.message_dict,
        )


class SequenciaDocumentoFiscalModelTests(SimpleTestCase):
    def test_defaults(self):
        sequencia = SequenciaDocumentoFiscal(
            matriz_id=1,
            loja_id=1,
            modelo=ModeloDocumentoFiscal.NFCE,
            ambiente=AmbienteDocumentoFiscal.HOMOLOGACAO,
            serie=1,
        )

        self.assertEqual(
            sequencia.proximo_numero,
            1,
        )