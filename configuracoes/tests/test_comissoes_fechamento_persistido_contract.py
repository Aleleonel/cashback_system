from django.test import TestCase

class FechamentoPersistidoContractTest(TestCase):
    def test_servico_publico_de_fechamento_persistido_existe(self):
        from configuracoes.services_comissoes import fechar_comissoes_competencia
        self.assertTrue(callable(fechar_comissoes_competencia))