from django.test import SimpleTestCase

from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja


class SecretsCertificadoA1ModeloContractTests(SimpleTestCase):
    def test_modelo_expoe_referencia_opaca_separada(self):
        field = ConfiguracaoEmissaoFiscalLoja._meta.get_field(
            "certificado_a1_segredo_referencia"
        )
        self.assertEqual(field.max_length, 500)
        self.assertTrue(field.blank)
        self.assertEqual(field.default, "")

    def test_modelo_nao_persiste_campo_de_senha_a1(self):
        nomes = {
            field.name.lower()
            for field in ConfiguracaoEmissaoFiscalLoja._meta.get_fields()
        }
        proibidos = {
            "certificado_a1_senha",
            "senha_certificado_a1",
            "senha_a1",
            "password_a1",
            "secret_a1",
        }
        self.assertTrue(nomes.isdisjoint(proibidos))
