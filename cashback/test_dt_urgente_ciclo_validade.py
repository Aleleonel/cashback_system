from datetime import timedelta
from django.test import SimpleTestCase
from cashback.services.compra import calcular_datas_cashback

class CicloValidadeCashbackContratoTests(SimpleTestCase):
    def test_expiracao_e_contada_apos_liberacao(self):
        compra, liberacao, expiracao = calcular_datas_cashback(dias_liberacao=7, dias_expiracao=45)
        self.assertEqual(liberacao, compra + timedelta(days=7))
        self.assertEqual(expiracao, liberacao + timedelta(days=45))

    def test_expiracao_zero_expira_na_liberacao_e_nunca_antes(self):
        compra, liberacao, expiracao = calcular_datas_cashback(dias_liberacao=7, dias_expiracao=0)
        self.assertEqual(liberacao, compra + timedelta(days=7))
        self.assertEqual(expiracao, liberacao)
        self.assertGreaterEqual(expiracao, liberacao)