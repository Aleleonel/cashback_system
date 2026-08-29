from types import SimpleNamespace
from unittest.mock import Mock
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from empresa.services import avaliar_prontidao_fiscal_loja
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja

class LojaSemConfiguracao:
    cnpj="12345678000195"
    @property
    def configuracao_emissao_fiscal(self): raise ConfiguracaoEmissaoFiscalLoja.DoesNotExist

class ProntidaoFiscal195CFG4BTests(SimpleTestCase):

    def test_serie_mil_gera_pendencia(self):
        configuracao = self.cfg()
        configuracao.serie_nfce = 1000
        resultado = avaliar_prontidao_fiscal_loja(self.loja(configuracao))
        self.assertEqual(resultado["status"], "pendencias")
        self.assertTrue(any("999" in item for item in resultado["pendencias"]))

    def test_prontidao_valida_copia_sem_mutar_original(self):
        class ConfigFake:
            ativa = True
            serie_nfce = 1

            def __init__(self):
                self.uf = "SP"

            def __copy__(self):
                copia = ConfigFake()
                copia.uf = self.uf
                return copia

            def full_clean(self):
                self.uf = "RJ"

        configuracao = ConfigFake()
        resultado = avaliar_prontidao_fiscal_loja(self.loja(configuracao))
        self.assertEqual(resultado["status"], "configurada")
        self.assertEqual(configuracao.uf, "SP")

    def cfg(self,ativa=True,erro=None):
        c=SimpleNamespace(serie_nfce=1, ativa=ativa);c.full_clean=Mock();c.full_clean.side_effect=erro;return c
    def loja(self,c,cnpj="12345678000195"): return SimpleNamespace(cnpj=cnpj,configuracao_emissao_fiscal=c)
    def test_incompleta(self): self.assertEqual(avaliar_prontidao_fiscal_loja(LojaSemConfiguracao())["status"],"incompleta")
    def test_inativa(self):
        c=self.cfg(False);r=avaliar_prontidao_fiscal_loja(self.loja(c));self.assertEqual(r["status"],"inativa");c.full_clean.assert_not_called()
    def test_cnpj_invalido(self):
        r=avaliar_prontidao_fiscal_loja(self.loja(self.cfg(),"12.345"));self.assertEqual(r["status"],"pendencias");self.assertTrue(any("CNPJ" in x for x in r["pendencias"]))
    def test_model_invalido(self):
        r=avaliar_prontidao_fiscal_loja(self.loja(self.cfg(True,ValidationError({"cep":["CEP invalido."]}))));self.assertEqual(r["status"],"pendencias")
    def test_pronta(self):
        r=avaliar_prontidao_fiscal_loja(self.loja(self.cfg()));self.assertEqual(r["status"],"configurada");self.assertEqual(r["label"],"Pronta")
    def test_cnpj_formatado(self): self.assertEqual(avaliar_prontidao_fiscal_loja(self.loja(self.cfg(),"12.345.678/0001-95"))["status"],"configurada")
