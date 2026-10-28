from datetime import date
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from relatorios.services_dre import ResultadoDRE

class DREHTTPPeriodoTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.user=U.objects.create_superuser(username="f25d41_admin",email="f25d41@example.test",password="TesteF25D41!")
        self.user.ativo = True
        self.user.save(update_fields=["ativo"])
        from empresas.models import Matriz
        self.matriz = Matriz.objects.create(nome="Matriz F25D41", status="ativa")
        self.client.force_login(self.user)
        self.zero=ResultadoDRE(receita_bruta=0,acrescimos=0,deducoes_receita=0,receita_liquida=0,cmv=0,lucro_bruto=0,despesas_operacionais=0,resultado_operacional=0,resultado_financeiro=0,outras_receitas_despesas=0,resultado_antes_impostos=0,margem_bruta=0,margem_operacional=0,memoria_calculo={})

    def fake_apurar(self, chamadas):
        def fn(**kwargs):
            chamadas.append(kwargs)
            return {"resultado":self.zero,"analise_vertical":{},"drilldown":{},"comparativo":None}
        return fn

    @patch("relatorios.views.apurar_evolucao_mensal",return_value=[])
    def test_mes_completo_compara_mes_anterior_completo(self,_):
        chamadas=[]
        with patch("relatorios.views.apurar_dre",side_effect=self.fake_apurar(chamadas)):
            r=self.client.get(reverse("relatorios:dre"),{"matriz":self.matriz.pk,"data_inicio":"2026-09-01","data_fim":"2026-09-30"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(chamadas[0]["periodo_anterior"],(date(2026,8,1),date(2026,8,31)))

    @patch("relatorios.views.apurar_evolucao_mensal",return_value=[])
    def test_periodo_arbitrario_compara_intervalo_equivalente(self,_):
        chamadas=[]
        with patch("relatorios.views.apurar_dre",side_effect=self.fake_apurar(chamadas)):
            r=self.client.get(reverse("relatorios:dre"),{"matriz":self.matriz.pk,"data_inicio":"2026-09-10","data_fim":"2026-09-19"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(chamadas[0]["periodo_anterior"],(date(2026,8,31),date(2026,9,9)))

    @patch("relatorios.views.apurar_evolucao_mensal",return_value=[])
    def test_data_invalida_sinaliza_erro_no_contexto(self,_):
        chamadas=[]
        with patch("relatorios.views.apurar_dre",side_effect=self.fake_apurar(chamadas)):
            r=self.client.get(reverse("relatorios:dre"),{"matriz":self.matriz.pk,"data_inicio":"2026-99-99","data_fim":"2026-09-30"})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.context["erro_filtros"])
        self.assertIn("Data inválida",r.context["erro_filtros"])

    @patch("relatorios.views.apurar_evolucao_mensal",return_value=[])
    def test_periodo_invertido_sinaliza_e_nao_inverte_silenciosamente(self,_):
        chamadas=[]
        with patch("relatorios.views.apurar_dre",side_effect=self.fake_apurar(chamadas)):
            r=self.client.get(reverse("relatorios:dre"),{"matriz":self.matriz.pk,"data_inicio":"2026-09-30","data_fim":"2026-09-01"})
        self.assertEqual(r.status_code,200)
        self.assertIn("Período inválido",r.context["erro_filtros"])
        self.assertEqual(chamadas, [])
