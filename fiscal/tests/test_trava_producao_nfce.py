from unittest.mock import Mock

from django.test import SimpleTestCase

from fiscal.services_transporte_sefaz import (
    TransporteSefazError,
    transmitir_autorizacao_nfce_sp,
    transmitir_consulta_protocolo_nfce_sp,
)


class TravaProducaoNFCeContractTests(SimpleTestCase):
    """
    Contrato de seguranca para a fase pre-homologacao real.

    Mesmo que ambiente='producao' chegue ao transporte por configuracao
    acidental, nenhuma tentativa de rede pode ocorrer enquanto a producao
    real nao estiver explicitamente habilitada por um mecanismo separado.
    """

    def test_autorizacao_producao_bloqueada_antes_de_ssl_e_rede(self):
        certificado = Mock()
        opener = Mock(side_effect=AssertionError("rede nao pode ser chamada"))

        with self.assertRaisesRegex(
            TransporteSefazError,
            "producao.*bloqueada|bloqueada.*producao",
        ):
            transmitir_autorizacao_nfce_sp(
                xml_envi_nfe=(
                    '<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" '
                    'versao="4.00"><idLote>1</idLote><indSinc>1</indSinc>'
                    '</enviNFe>'
                ),
                ambiente="producao",
                certificado_a1=certificado,
                opener=opener,
            )

        opener.assert_not_called()

    def test_consulta_producao_bloqueada_antes_de_ssl_e_rede(self):
        certificado = Mock()
        opener = Mock(side_effect=AssertionError("rede nao pode ser chamada"))

        with self.assertRaisesRegex(
            TransporteSefazError,
            "producao.*bloqueada|bloqueada.*producao",
        ):
            transmitir_consulta_protocolo_nfce_sp(
                chave_acesso="35260812345678000195650010000000011000000019",
                ambiente="producao",
                certificado_a1=certificado,
                opener=opener,
            )

        opener.assert_not_called()

    def test_homologacao_nao_e_bloqueada_pela_guarda_de_producao(self):
        """
        Este teste nao exige sucesso de TLS/rede. Ele apenas garante que
        homologacao nao recebe o erro reservado ao bloqueio de producao.
        """
        certificado = Mock()
        opener = Mock(side_effect=RuntimeError("sentinela apos guarda"))

        with self.assertRaises(Exception) as ctx:
            transmitir_autorizacao_nfce_sp(
                xml_envi_nfe=(
                    '<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" '
                    'versao="4.00"><idLote>1</idLote><indSinc>1</indSinc>'
                    '</enviNFe>'
                ),
                ambiente="homologacao",
                certificado_a1=certificado,
                opener=opener,
            )

        self.assertNotRegex(
            str(ctx.exception).lower(),
            "producao.*bloqueada|bloqueada.*producao",
        )
