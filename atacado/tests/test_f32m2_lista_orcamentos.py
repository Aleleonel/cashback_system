from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from atacado.models import OrcamentoAtacado
from clientes.models import Cliente
from empresas.models import Loja, Matriz


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class F32M2ListaOrcamentosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Matriz.objects.create(nome="F32M2 Matriz A")
        cls.b = Matriz.objects.create(nome="F32M2 Matriz B")
        cls.la = Loja.objects.create(matriz=cls.a, nome="F32M2 Loja A")
        cls.lb = Loja.objects.create(matriz=cls.b, nome="F32M2 Loja B")
        cls.ca = Cliente.objects.create(matriz=cls.a, loja_cadastro=cls.la, nome="Cliente Exclusivo A")
        cls.cb = Cliente.objects.create(matriz=cls.b, loja_cadastro=cls.lb, nome="Cliente Exclusivo B")
        cls.oa = OrcamentoAtacado.objects.create(matriz=cls.a, loja=cls.la, cliente=cls.ca)
        cls.ob = OrcamentoAtacado.objects.create(matriz=cls.b, loja=cls.lb, cliente=cls.cb)

    def login(self, perfil, matriz, username="f32m2_user"):
        u = get_user_model().objects.create_user(username=username, password="F32M2_Test!234")
        u.perfil = perfil
        u.matriz = matriz
        u.save()
        self.client.force_login(u)
        return u

    def test_master_isolamento(self):
        self.login("master", self.a)
        r = self.client.get(reverse("atacado:orcamentos_lista"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Cliente Exclusivo A")
        self.assertNotContains(r, "Cliente Exclusivo B")
        self.assertContains(r, reverse("atacado:orcamento_pdf", args=[self.oa.pk]))

    def test_admin_loja_isolamento(self):
        usuario = self.login("admin_loja", self.b)
        usuario.lojas.add(self.lb)
        r = self.client.get(reverse("atacado:orcamentos_lista"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Cliente Exclusivo B")
        self.assertNotContains(r, "Cliente Exclusivo A")

    def test_operador_loja_autorizada(self):
        usuario = self.login("operador", self.a)
        usuario.lojas.add(self.la)
        resposta = self.client.get(reverse("atacado:orcamentos_lista"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Cliente Exclusivo A")
        self.assertNotContains(resposta, "Cliente Exclusivo B")

    def test_superuser_selecao_explicita(self):
        u = get_user_model().objects.create_superuser(username="f32m2_super", email="f32m2@example.test", password="F32M2_Test!234")
        self.client.force_login(u)
        url = reverse("atacado:orcamentos_lista")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Cliente Exclusivo A")
        self.assertNotContains(r, "Cliente Exclusivo B")
        r = self.client.get(url, {"matriz": self.a.pk})
        self.assertContains(r, "Cliente Exclusivo A")
        self.assertNotContains(r, "Cliente Exclusivo B")
        self.assertContains(r, "?matriz=" + str(self.a.pk))
        self.assertEqual(self.client.get(url, {"matriz": "invalida"}).status_code, 404)

    def test_filtro_cliente(self):
        self.login("master", self.a)
        r = self.client.get(reverse("atacado:orcamentos_lista"), {"q": "NaoExiste"})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Cliente Exclusivo A")
