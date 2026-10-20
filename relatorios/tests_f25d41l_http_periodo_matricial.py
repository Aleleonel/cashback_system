from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from core.choices import StatusOperacional
from empresas.models import Matriz, Loja

class DREPeriodoPerfilMatricialHTTPTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="F25D41L Matriz")
        U=get_user_model()
        self.user=U.objects.create_user(
            username="f25d41l_fabricaadm",
            password="Teste123!@#",
            perfil="admin_loja",
            matriz=self.matriz,
            ativo=True,
        )
        self.loja=Loja.objects.create(matriz=self.matriz,nome="F25D41L Loja Ativa",cnpj="11.111.111/0001-11",status=StatusOperacional.ATIVA)
        self.user.lojas.add(self.loja)
        PermissaoUsuario.objects.create(usuario=self.user,permissao="relatorios.dashboard")
        self.client.force_login(self.user)
        self.url=reverse("relatorios:dre")

    def test_mes_calendario_completo_compara_mes_anterior_completo(self):
        r=self.client.get(self.url,{"data_inicio":"2026-09-01","data_fim":"2026-09-30"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["matriz"],self.matriz)
        self.assertEqual(r.context["periodo_anterior"],(date(2026,8,1),date(2026,8,31)))

    def test_periodo_arbitrario_compara_intervalo_anterior_de_mesma_duracao(self):
        r=self.client.get(self.url,{"data_inicio":"2026-09-10","data_fim":"2026-09-20"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["periodo_anterior"],(date(2026,8,30),date(2026,9,9)))

    def test_data_invalida_expoe_erro_sem_403(self):
        r=self.client.get(self.url,{"data_inicio":"invalida","data_fim":"2026-09-30"})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.context["erro_filtros"])
        self.assertIn("Data",r.context["erro_filtros"][0])

    def test_periodo_invertido_expoe_erro_sem_403(self):
        r=self.client.get(self.url,{"data_inicio":"2026-09-30","data_fim":"2026-09-01"})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.context["erro_filtros"])
        self.assertTrue(any("odo" in str(x) for x in r.context["erro_filtros"]))

    def test_query_matriz_nao_desvia_fabricaadm(self):
        outra=Matriz.objects.create(nome="F25D41L Outra")
        r=self.client.get(self.url,{"matriz":str(outra.pk),"data_inicio":"2026-09-01","data_fim":"2026-09-30"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["matriz"].pk,self.matriz.pk)
        self.assertNotEqual(r.context["matriz"].pk,outra.pk)