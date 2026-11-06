from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from atacado.models import OrcamentoAtacado, PedidoAtacado
from clientes.models import Cliente
from empresas.models import Loja, Matriz


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class F32L9GPermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Matriz.objects.create(nome="F32L9G Matriz A")
        cls.b = Matriz.objects.create(nome="F32L9G Matriz B")
        cls.la = Loja.objects.create(matriz=cls.a, nome="F32L9G Loja A")
        cls.lb = Loja.objects.create(matriz=cls.b, nome="F32L9G Loja B")
        cls.ca = Cliente.objects.create(matriz=cls.a, loja_cadastro=cls.la, nome="F32L9G Cliente A")
        cls.cb = Cliente.objects.create(matriz=cls.b, loja_cadastro=cls.lb, nome="F32L9G Cliente B")
        cls.oa = OrcamentoAtacado.objects.create(matriz=cls.a, loja=cls.la, cliente=cls.ca)
        cls.ob = OrcamentoAtacado.objects.create(matriz=cls.b, loja=cls.lb, cliente=cls.cb)
        cls.pa = PedidoAtacado.objects.create(orcamento_origem=cls.oa, matriz=cls.a, loja=cls.la, cliente=cls.ca)
        cls.pb = PedidoAtacado.objects.create(orcamento_origem=cls.ob, matriz=cls.b, loja=cls.lb, cliente=cls.cb)

    def urls(self, orcamento, pedido):
        for tipo, obj in (("orcamento", orcamento), ("pedido", pedido)):
            for formato in ("pdf", "xlsx"):
                yield reverse("atacado:" + tipo + "_" + formato, args=[obj.pk])

    def login(self, *, username, perfil, matriz, ativo=True, loja=None):
        user = get_user_model().objects.create_user(
            username=username, password="F32L9G_Test!234",
        )
        user.perfil = perfil
        user.matriz = matriz
        user.ativo = ativo
        user.save()
        if loja is not None:
            user.lojas.add(loja)
        self.client.force_login(user)
        return user

    def test_admin_master_matriz_a_acessa_apenas_proprios_documentos(self):
        self.login(username="f32l9g_master", perfil="master", matriz=self.a)
        for url in self.urls(self.oa, self.pa):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        for url in self.urls(self.ob, self.pb):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_admin_loja_matriz_a_acessa_apenas_proprios_documentos(self):
        self.login(username="f32l9g_admin", perfil="admin_loja", matriz=self.a, loja=self.la)
        for url in self.urls(self.oa, self.pa):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        for url in self.urls(self.ob, self.pb):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_operador_autorizado_acessa_documentos(self):
        self.login(username="f32l9g_operador", perfil="operador", matriz=self.a, loja=self.la)
        for url in self.urls(self.oa, self.pa):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        for url in self.urls(self.ob, self.pb):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_administrador_inativo_recebe_403(self):
        self.login(username="f32l9g_inativo", perfil="master", matriz=self.a, ativo=False)
        for url in self.urls(self.oa, self.pa):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_documentos_inexistentes_retornam_404(self):
        self.login(username="f32l9g_inexistente", perfil="master", matriz=self.a)
        for tipo in ("orcamento", "pedido"):
            for formato in ("pdf", "xlsx"):
                url = reverse("atacado:" + tipo + "_" + formato, args=[999999999])
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 404)

    def test_superuser_matriz_invalida_retorna_404(self):
        user = get_user_model().objects.create_superuser(
            username="f32l9g_superuser", email="f32l9g@example.test", password="F32L9G_Test!234"
        )
        self.client.force_login(user)
        for url in self.urls(self.oa, self.pa):
            for matriz in ("", "invalida", "999999999"):
                with self.subTest(url=url, matriz=matriz):
                    self.assertEqual(self.client.get(url, {"matriz": matriz}).status_code, 404)
    def test_admin_e_operador_bloqueados_em_outra_loja_da_mesma_matriz(self):
        outra = Loja.objects.create(matriz=self.a, nome="F32M4N Loja nao autorizada")
        cliente = Cliente.objects.create(matriz=self.a, loja_cadastro=outra, nome="F32M4N Cliente isolado")
        orcamento = OrcamentoAtacado.objects.create(matriz=self.a, loja=outra, cliente=cliente)
        pedido = PedidoAtacado.objects.create(orcamento_origem=orcamento, matriz=self.a, loja=outra, cliente=cliente)
        for perfil in ("admin_loja", "operador"):
            self.client.logout()
            self.login(username="f32m4n_" + perfil, perfil=perfil, matriz=self.a, loja=self.la)
            for url in self.urls(orcamento, pedido):
                with self.subTest(perfil=perfil, url=url):
                    self.assertEqual(self.client.get(url).status_code, 404)
