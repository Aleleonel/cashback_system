from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from fiscal.choices_documento_fiscal import (
    StatusDocumentoFiscal,
)
from fiscal.services_documento_fiscal import (
    TRANSICOES_PERMITIDAS,
    transicionar_documento_fiscal,
    validar_transicao_documento_fiscal,
)


def documento_fake(status):
    return SimpleNamespace(
        status=status,
        codigo_status="",
        motivo_status="",
        protocolo_autorizacao="",
        data_autorizacao=None,
        tentativa_atual=0,
        ultima_tentativa_em=None,
        save=lambda: None,
    )


class MaquinaEstadosDocumentoFiscalTests(SimpleTestCase):
    def test_estados_previstos_no_contrato(self):
        esperados = {
            StatusDocumentoFiscal.RASCUNHO,
            StatusDocumentoFiscal.PREPARADO,
            StatusDocumentoFiscal.PENDENTE_TRANSMISSAO,
            StatusDocumentoFiscal.TRANSMITINDO,
            StatusDocumentoFiscal.AUTORIZADO,
            StatusDocumentoFiscal.REJEITADO,
            StatusDocumentoFiscal.DENEGADO,
            StatusDocumentoFiscal.CONTINGENCIA,
            StatusDocumentoFiscal.CANCELADO,
            StatusDocumentoFiscal.ERRO,
        }

        self.assertEqual(
            set(TRANSICOES_PERMITIDAS),
            esperados,
        )

    def test_rascunho_para_preparado(self):
        validar_transicao_documento_fiscal(
            status_atual=StatusDocumentoFiscal.RASCUNHO,
            novo_status=StatusDocumentoFiscal.PREPARADO,
        )

    def test_bloqueia_rascunho_para_autorizado(self):
        with self.assertRaises(ValidationError):
            validar_transicao_documento_fiscal(
                status_atual=StatusDocumentoFiscal.RASCUNHO,
                novo_status=StatusDocumentoFiscal.AUTORIZADO,
            )

    def test_transmitindo_incrementa_tentativa(self):
        documento = documento_fake(
            StatusDocumentoFiscal.PENDENTE_TRANSMISSAO
        )

        transicionar_documento_fiscal(
            documento=documento,
            novo_status=StatusDocumentoFiscal.TRANSMITINDO,
            salvar=False,
        )

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.TRANSMITINDO,
        )
        self.assertEqual(
            documento.tentativa_atual,
            1,
        )
        self.assertIsNotNone(
            documento.ultima_tentativa_em
        )

    def test_autorizado_exige_protocolo(self):
        documento = documento_fake(
            StatusDocumentoFiscal.TRANSMITINDO
        )

        with self.assertRaises(ValidationError) as erro:
            transicionar_documento_fiscal(
                documento=documento,
                novo_status=StatusDocumentoFiscal.AUTORIZADO,
                salvar=False,
            )

        self.assertIn(
            "protocolo_autorizacao",
            erro.exception.message_dict,
        )

    def test_transmitindo_para_autorizado_com_protocolo(self):
        documento = documento_fake(
            StatusDocumentoFiscal.TRANSMITINDO
        )

        transicionar_documento_fiscal(
            documento=documento,
            novo_status=StatusDocumentoFiscal.AUTORIZADO,
            protocolo_autorizacao="PROTOCOLO-TESTE",
            salvar=False,
        )

        self.assertEqual(
            documento.status,
            StatusDocumentoFiscal.AUTORIZADO,
        )
        self.assertEqual(
            documento.protocolo_autorizacao,
            "PROTOCOLO-TESTE",
        )
        self.assertIsNotNone(
            documento.data_autorizacao
        )

    def test_autorizado_para_cancelado(self):
        validar_transicao_documento_fiscal(
            status_atual=StatusDocumentoFiscal.AUTORIZADO,
            novo_status=StatusDocumentoFiscal.CANCELADO,
        )

    def test_cancelado_nao_volta_para_autorizado(self):
        with self.assertRaises(ValidationError):
            validar_transicao_documento_fiscal(
                status_atual=StatusDocumentoFiscal.CANCELADO,
                novo_status=StatusDocumentoFiscal.AUTORIZADO,
            )