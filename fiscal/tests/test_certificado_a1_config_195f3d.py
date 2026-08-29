from pathlib import Path

from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja


class CertificadoA1Config195F3DTests(TestCase):
    def setUp(self):
        matriz = Matriz.objects.create(nome="Matriz 195F3D")
        self.loja = Loja.objects.create(
            matriz=matriz,
            nome="Loja 195F3D",
            cnpj="12345678000199",
        )

    def test_modelo_expoe_apenas_referencia_nao_secreta_do_a1(self):
        campo = ConfiguracaoEmissaoFiscalLoja._meta.get_field("certificado_a1_referencia")
        self.assertEqual(campo.max_length, 255)
        self.assertTrue(campo.blank)
        self.assertEqual(campo.default, "")

    def test_referencia_e_opcional_na_fundacao(self):
        obj = ConfiguracaoEmissaoFiscalLoja(
            loja=self.loja,
            razao_social="Loja Fiscal Ltda",
            inscricao_estadual="123456789",
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            municipio="Sao Paulo",
            codigo_municipio_ibge="3550308",
            uf="SP",
            cep="01001000",
            crt="3",
            serie_nfce=1,
        )
        obj.full_clean()

    def test_form_operacional_nao_expoe_referencia_do_certificado(self):
        from empresa.forms import ConfiguracaoFiscalLojaEmpresaForm
        self.assertNotIn("certificado_a1_referencia", ConfiguracaoFiscalLojaEmpresaForm._meta.fields)

    def test_gitignore_protege_formatos_de_certificado(self):
        texto = (Path(__file__).resolve().parents[2] / ".gitignore").read_text(encoding="utf-8")
        for regra in ("*.pfx", "*.p12", "*.pem", "*.key", "*.crt", "*.cer"):
            self.assertIn(regra, texto)