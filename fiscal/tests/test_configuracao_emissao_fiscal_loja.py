from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Loja, Matriz
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja


class ConfiguracaoEmissaoFiscalLojaTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Fiscal")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Fiscal",
            cnpj="12345678000199",
        )

    def configuracao(self, **overrides):
        dados = {
            "loja": self.loja,
            "razao_social": "Loja Fiscal Ltda",
            "nome_fantasia": "Loja Fiscal",
            "inscricao_estadual": "123456789",
            "logradouro": "Rua Teste",
            "numero": "100",
            "bairro": "Centro",
            "municipio": "Sao Paulo",
            "codigo_municipio_ibge": "3550308",
            "uf": "SP",
            "cep": "01001000",
            "crt": "3",
            "serie_nfce": 1,
        }
        dados.update(overrides)
        return ConfiguracaoEmissaoFiscalLoja(**dados)

    def test_configuracao_valida(self):
        self.configuracao().full_clean()

    def test_rejeita_codigo_ibge_invalido(self):
        with self.assertRaises(ValidationError):
            self.configuracao(codigo_municipio_ibge="123").full_clean()

    def test_rejeita_cep_invalido(self):
        with self.assertRaises(ValidationError):
            self.configuracao(cep="123").full_clean()

    def test_normaliza_uf_e_cep(self):
        obj = self.configuracao(uf="sp", cep="01001000")
        obj.full_clean()
        self.assertEqual(obj.uf, "SP")
        self.assertEqual(obj.cep, "01001000")
