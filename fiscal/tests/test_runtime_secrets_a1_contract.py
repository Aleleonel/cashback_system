from inspect import signature

from django.test import SimpleTestCase

from fiscal.services_assinatura_documento_fiscal import assinar_documento_fiscal
from fiscal.services_execucao_autorizacao import (
    executar_autorizacao_nfce_sp,
    executar_consulta_protocolo_nfce_sp,
)


class RuntimeSecretsA1PublicContractTests(SimpleTestCase):
    def _assert_contrato_seguro(self, funcao):
        parametros = signature(funcao).parameters
        self.assertNotIn("senha_certificado", parametros)
        self.assertNotIn("senha_certificado_a1", parametros)
        self.assertIn("resolvedor_senha", parametros)

    def test_assinatura_nao_recebe_senha_publica(self):
        self._assert_contrato_seguro(assinar_documento_fiscal)

    def test_autorizacao_nao_recebe_senha_publica(self):
        self._assert_contrato_seguro(executar_autorizacao_nfce_sp)

    def test_consulta_nao_recebe_senha_publica(self):
        self._assert_contrato_seguro(executar_consulta_protocolo_nfce_sp)
