from django.test import TestCase

from financeiro.models import TituloFinanceiro


class F24IntegracaoComissaoFinanceiroContratoRedTests(TestCase):
    def test_financeiro_expoe_origem_especifica_comissao(self):
        self.assertTrue(
            hasattr(TituloFinanceiro.OrigemTipo, "COMISSAO"),
            "F24 exige OrigemTipo.COMISSAO; nao usar MANUAL para obrigacao gerada por snapshot.",
        )

    def test_origem_comissao_faz_parte_dos_choices_publicos(self):
        self.assertIn(
            "COMISSAO",
            TituloFinanceiro.OrigemTipo.values,
            "Origem financeira de comissao deve ser rastreavel como dominio proprio.",
        )