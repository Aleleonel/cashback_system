from datetime import datetime, timezone
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from fiscal.services_chave_acesso import (
    calcular_digito_verificador_chave, codigo_uf_ibge,
    construir_chave_acesso, gerar_codigo_numerico,
)

class ChaveAcessoNFCeTests(SimpleTestCase):
    def test_codigo_uf_sp(self):
        self.assertEqual(codigo_uf_ibge("SP"), "35")

    def test_rejeita_uf_invalida(self):
        with self.assertRaises(ValidationError):
            codigo_uf_ibge("XX")

    def test_modulo_11_vetor_conhecido(self):
        base = "3526081234567800019565001000000001112345678"
        self.assertEqual(len(base), 43)
        self.assertEqual(calcular_digito_verificador_chave(base), "0")

    def test_constroi_chave_44_digitos(self):
        i = construir_chave_acesso(
            uf="SP", data_emissao=datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
            cnpj="12.345.678/0001-95", modelo="65", serie=1, numero=1,
            tipo_emissao="1", codigo_numerico="12345678",
        )
        self.assertEqual(i.chave_acesso, "35260812345678000195650010000000011123456780")
        self.assertEqual(len(i.chave_acesso), 44)
        self.assertEqual(i.codigo_numerico, "12345678")
        self.assertEqual(i.digito_verificador, "0")

    def test_rejeita_cnpj_invalido(self):
        with self.assertRaises(ValidationError):
            construir_chave_acesso(uf="SP", data_emissao=datetime(2026,8,21),
                cnpj="123", modelo="65", serie=1, numero=1, codigo_numerico="12345678")

    def test_rejeita_codigo_numerico_invalido(self):
        with self.assertRaises(ValidationError):
            construir_chave_acesso(uf="SP", data_emissao=datetime(2026,8,21),
                cnpj="12345678000195", modelo="65", serie=1, numero=1,
                codigo_numerico="123")

    @patch("fiscal.services_chave_acesso.secrets.randbelow", return_value=42)
    def test_codigo_numerico_tem_oito_digitos(self, mocked):
        self.assertEqual(gerar_codigo_numerico(), "00000042")
        mocked.assert_called_once_with(100_000_000)
