from django.test import TestCase
from django.urls import reverse

from configuracoes.forms_atacado import FaixaAtacadoFormSet, PoliticaAtacadoForm
from configuracoes.models import ConfiguracaoComercial, FaixaAtacado
from empresas.models import Matriz


class F32DPoliticaAtacadoUITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz F32D", cnpj="33333333000191")
        cls.config = ConfiguracaoComercial.objects.create(matriz=cls.matriz)

    def test_url_politica_atacado_existe(self):
        self.assertEqual(reverse("configuracoes:politica_atacado"), "/configuracoes/vendas-comissoes/atacado/")

    def test_form_geral_expoe_politica_promocional(self):
        form = PoliticaAtacadoForm(instance=self.config)
        self.assertIn("atacado_ativo", form.fields)
        self.assertIn("produto_promocional_conta_para_faixa_atacado", form.fields)

    def test_formset_rejeita_sobreposicao_entre_novas_faixas(self):
        data = {
            "faixas-TOTAL_FORMS": "2", "faixas-INITIAL_FORMS": "0",
            "faixas-MIN_NUM_FORMS": "0", "faixas-MAX_NUM_FORMS": "1000",
            "faixas-0-valor_minimo": "1000.00", "faixas-0-valor_maximo": "2000.00", "faixas-0-percentual_desconto": "5.00",
            "faixas-1-valor_minimo": "1500.00", "faixas-1-valor_maximo": "3000.00", "faixas-1-percentual_desconto": "8.00",
        }
        formset = FaixaAtacadoFormSet(data=data, instance=self.config, prefix="faixas")
        self.assertFalse(formset.is_valid())
        self.assertIn("nao podem se sobrepor", " ".join(formset.non_form_errors()).lower())

    def test_formset_aceita_tres_faixas_progressivas(self):
        data = {
            "faixas-TOTAL_FORMS": "3", "faixas-INITIAL_FORMS": "0",
            "faixas-MIN_NUM_FORMS": "0", "faixas-MAX_NUM_FORMS": "1000",
            "faixas-0-valor_minimo": "1000.00", "faixas-0-valor_maximo": "1999.99", "faixas-0-percentual_desconto": "5.00",
            "faixas-1-valor_minimo": "2000.00", "faixas-1-valor_maximo": "4999.99", "faixas-1-percentual_desconto": "8.00",
            "faixas-2-valor_minimo": "5000.00", "faixas-2-valor_maximo": "", "faixas-2-percentual_desconto": "12.00",
        }
        formset = FaixaAtacadoFormSet(data=data, instance=self.config, prefix="faixas")
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.assertEqual(FaixaAtacado.objects.filter(configuracao=self.config).count(), 3)
