from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import PlanoConta


class PlanoContaLabelR9KUXTests(TestCase):
    def test_str_exibe_codigo_e_nome(self):
        matriz = Matriz.objects.create(nome="Matriz Label Plano R9KUX")
        plano = PlanoConta.objects.create(
            matriz=matriz,
            codigo="5.01",
            nome="Despesas Operacionais",
            tipo=PlanoConta.Tipo.ANALITICA,
            natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True,
            ativo=True,
        )
        self.assertEqual(str(plano), "5.01 - Despesas Operacionais")