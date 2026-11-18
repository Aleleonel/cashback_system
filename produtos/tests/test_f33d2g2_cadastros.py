from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse, resolve
from empresas.models import Matriz
from produtos.models import ApresentacaoProduto, ModeloCaixaExpedicao, CapacidadeReferenciaCaixa
from produtos.forms.logistica import CapacidadeCaixaForm, ApresentacaoLogisticaForm, CaixaExpedicaoForm

class F33D2G2CadastrosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Matriz.objects.create(nome='F33G2 Matriz A')
        cls.b = Matriz.objects.create(nome='F33G2 Matriz B')
        cls.caixa_a = ModeloCaixaExpedicao.objects.create(matriz=cls.a, nome='Caixa A', largura_cm=30, altura_cm=30, comprimento_cm=30)
        cls.caixa_b = ModeloCaixaExpedicao.objects.create(matriz=cls.b, nome='Caixa B', largura_cm=30, altura_cm=30, comprimento_cm=30)
        cls.ap_a = ApresentacaoProduto.objects.create(matriz=cls.a, nome='Pote A', tipo='POTE')
        cls.ap_b = ApresentacaoProduto.objects.create(matriz=cls.b, nome='Pote B', tipo='POTE')

    def test_capacidade_form_filtra_caixas_e_apresentacoes(self):
        f = CapacidadeCaixaForm(matriz=self.a)
        self.assertIn(self.caixa_a, f.fields['caixa'].queryset)
        self.assertNotIn(self.caixa_b, f.fields['caixa'].queryset)
        self.assertIn(self.ap_a, f.fields['apresentacao'].queryset)
        self.assertNotIn(self.ap_b, f.fields['apresentacao'].queryset)

    def test_capacidade_form_rejeita_caixa_ou_apresentacao_de_outra_matriz(self):
        f = CapacidadeCaixaForm(data={'caixa':self.caixa_b.pk, 'apresentacao':self.ap_a.pk, 'quantidade':27}, matriz=self.a)
        self.assertFalse(f.is_valid())
        f = CapacidadeCaixaForm(data={'caixa':self.caixa_a.pk, 'apresentacao':self.ap_b.pk, 'quantidade':27}, matriz=self.a)
        self.assertFalse(f.is_valid())

    def test_capacidade_form_aceita_relacionamento_da_mesma_matriz(self):
        f = CapacidadeCaixaForm(data={'caixa':self.caixa_a.pk, 'apresentacao':self.ap_a.pk, 'quantidade':27}, matriz=self.a)
        self.assertTrue(f.is_valid(), f.errors)

    def test_capacidade_modelo_rejeita_troca_de_matriz(self):
        with self.assertRaises(ValidationError):
            CapacidadeReferenciaCaixa.objects.create(matriz=self.a, caixa=self.caixa_a, apresentacao=self.ap_b, quantidade=27)

    def test_refil_form_sem_profundidade(self):
        f = ApresentacaoLogisticaForm(data={'nome':'Refil 40x50', 'tipo':'REFIL', 'largura_cm':'40', 'altura_cm':'50', 'profundidade_cm':'3', 'ativo':True})
        self.assertFalse(f.is_valid())

    def test_caixa_form_valida_dimensoes(self):
        f = CaixaExpedicaoForm(data={'nome':'Caixa valida', 'largura_cm':'50', 'altura_cm':'30', 'comprimento_cm':'40', 'ativo':True})
        self.assertTrue(f.is_valid(), f.errors)

    def test_rotas_logisticas_resolvem(self):
        for tipo in ('apresentacoes','caixas','capacidades'):
            for nome,kwargs in [('logistica_lista',{}),('logistica_novo',{}),('logistica_editar',{'item_id':1})]:
                url = reverse('produtos:'+nome, kwargs={'tipo':tipo,**kwargs})
                self.assertIsNotNone(resolve(url).func)
