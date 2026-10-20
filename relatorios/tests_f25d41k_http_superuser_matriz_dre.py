from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Matriz

class DRESuperuserMatrizHTTPTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.user=U.objects.create_superuser(username="f25d41k_admin",password="Teste123!@#")
        self.client.force_login(self.user)
        self.m1=Matriz.objects.create(nome="F25D41K Matriz A")
        self.m2=Matriz.objects.create(nome="F25D41K Matriz B")
        self.url=reverse("relatorios:dre")

    def test_superuser_sem_matriz_renderiza_seletor_sem_calcular(self):
        r=self.client.get(self.url)
        self.assertEqual(r.status_code,200)
        self.assertIsNone(r.context["matriz"])
        self.assertIn("Selecione uma matriz",r.context["erro_filtros"])
        self.assertIsNone(r.context["resultado"])
        self.assertContains(r,'name="matriz"')
        self.assertContains(r,self.m1.nome)
        self.assertContains(r,self.m2.nome)

    def test_superuser_com_matriz_valida_apura_no_escopo_escolhido(self):
        r=self.client.get(self.url,{"matriz":str(self.m2.pk)})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["matriz"].pk,self.m2.pk)
        self.assertEqual(r.context["matriz_filtro"],str(self.m2.pk))
        self.assertIsNotNone(r.context["resultado"])

    def test_superuser_matriz_inexistente_nao_faz_fallback(self):
        r=self.client.get(self.url,{"matriz":"999999999"})
        self.assertEqual(r.status_code,200)
        self.assertIsNone(r.context["matriz"])
        self.assertIsNone(r.context["resultado"])
        self.assertIn("Selecione uma matriz",r.context["erro_filtros"])

    def test_troca_explicita_de_matriz_altera_contexto(self):
        a=self.client.get(self.url,{"matriz":str(self.m1.pk)})
        b=self.client.get(self.url,{"matriz":str(self.m2.pk)})
        self.assertEqual(a.status_code,200);self.assertEqual(b.status_code,200)
        self.assertEqual(a.context["matriz"].pk,self.m1.pk)
        self.assertEqual(b.context["matriz"].pk,self.m2.pk)
        self.assertNotEqual(a.context["matriz"].pk,b.context["matriz"].pk)