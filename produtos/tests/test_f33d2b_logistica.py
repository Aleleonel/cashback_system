from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz
from produtos.models import ApresentacaoProduto, ModeloCaixaExpedicao, CapacidadeReferenciaCaixa


class LogisticaModelosTests(TestCase):
    def setUp(self):
        self.a = Matriz.objects.create(nome='Matriz A')
        self.b = Matriz.objects.create(nome='Matriz B')

    def test_refil_sem_profundidade_rigida(self):
        item = ApresentacaoProduto(matriz=self.a, nome='Refil 40x50', tipo='REFIL', largura_cm=40, altura_cm=50)
        item.full_clean()
        item.profundidade_cm = Decimal('2')
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_capacidade_isolamento_matriz(self):
        caixa = ModeloCaixaExpedicao.objects.create(matriz=self.a, nome='30x30x30', largura_cm=30, altura_cm=30, comprimento_cm=30)
        apresentacao = ApresentacaoProduto.objects.create(matriz=self.b, nome='Pote 100g', tipo='POTE')
        with self.assertRaises(ValidationError):
            CapacidadeReferenciaCaixa.objects.create(matriz=self.a, caixa=caixa, apresentacao=apresentacao, quantidade=27)

    def test_capacidade_positiva(self):
        caixa = ModeloCaixaExpedicao.objects.create(matriz=self.a, nome='50x30x40', largura_cm=50, altura_cm=30, comprimento_cm=40)
        apresentacao = ApresentacaoProduto.objects.create(matriz=self.a, nome='Pote 300g', tipo='POTE')
        with self.assertRaises(ValidationError):
            CapacidadeReferenciaCaixa.objects.create(matriz=self.a, caixa=caixa, apresentacao=apresentacao, quantidade=0)
        capacidade = CapacidadeReferenciaCaixa.objects.create(matriz=self.a, caixa=caixa, apresentacao=apresentacao, quantidade=23)
        self.assertEqual(capacidade.quantidade, 23)
