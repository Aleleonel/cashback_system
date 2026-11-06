from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from atacado.models import OrcamentoAtacado, PedidoAtacado


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class F32L9EHTTPExportsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Matriz.objects.create(nome="F32L9E Matriz A")
        cls.b = Matriz.objects.create(nome="F32L9E Matriz B")
        cls.la = Loja.objects.create(matriz=cls.a, nome="F32L9E Loja A")
        cls.lb = Loja.objects.create(matriz=cls.b, nome="F32L9E Loja B")
        cls.ca = Cliente.objects.create(matriz=cls.a, loja_cadastro=cls.la, nome="Cliente A")
        cls.cb = Cliente.objects.create(matriz=cls.b, loja_cadastro=cls.lb, nome="Cliente B")
        cls.oa = OrcamentoAtacado.objects.create(matriz=cls.a, loja=cls.la, cliente=cls.ca, numero=991001)
        cls.ob = OrcamentoAtacado.objects.create(matriz=cls.b, loja=cls.lb, cliente=cls.cb, numero=991002)
        cls.pa = PedidoAtacado.objects.create(orcamento_origem=cls.oa, matriz=cls.a, loja=cls.la, cliente=cls.ca)
        cls.pb = PedidoAtacado.objects.create(orcamento_origem=cls.ob, matriz=cls.b, loja=cls.lb, cliente=cls.cb)

    def _url(self, tipo, formato, obj):
        return reverse("atacado:" + tipo + "_" + formato, args=[obj.pk])

    def test_anonimo_redirecionado_nas_quatro_rotas(self):
        for tipo, obj in (("orcamento", self.oa), ("pedido", self.pa)):
            for formato in ("pdf", "xlsx"):
                with self.subTest(tipo=tipo, formato=formato):
                    self.assertEqual(self.client.get(self._url(tipo, formato, obj)).status_code, 302)

    def test_superuser_exige_matriz_explicita_e_bloqueia_matriz_errada(self):
        user_model = get_user_model()
        user = user_model.objects.create_superuser(
            username="f32l9e_root", email="f32l9e@example.test", password="F32l9e_Test!234"
        )
        self.client.force_login(user)
        for tipo, obj in (("orcamento", self.oa), ("pedido", self.pa)):
            for formato in ("pdf", "xlsx"):
                url = self._url(tipo, formato, obj)
                with self.subTest(tipo=tipo, formato=formato):
                    self.assertEqual(self.client.get(url).status_code, 404)
                    self.assertEqual(self.client.get(url, {"matriz": self.b.pk}).status_code, 404)

    def test_administrador_outra_matriz_recebe_404(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="f32l9e_admin", email="f32l9e_admin@example.test",
            password="F32l9e_Test!234",
        )
        user.is_superuser = False
        user.ativo = True
        user.perfil = "master"
        user.matriz = self.b
        user.save()
        self.client.force_login(user)
        for tipo, obj in (("orcamento", self.oa), ("pedido", self.pa)):
            for formato in ("pdf", "xlsx"):
                with self.subTest(tipo=tipo, formato=formato):
                    self.assertEqual(self.client.get(self._url(tipo, formato, obj)).status_code, 404)

    def test_superuser_download_binario_real(self):
        user_model = get_user_model()
        user = user_model.objects.create_superuser(
            username="f32l9e_download", email="f32l9e_dl@example.test",
            password="F32l9e_Test!234"
        )
        self.client.force_login(user)
        for tipo, obj in (("orcamento", self.oa), ("pedido", self.pa)):
            pdf = self.client.get(self._url(tipo, "pdf", obj), {"matriz": self.a.pk})
            self.assertEqual(pdf.status_code, 200)
            self.assertEqual(pdf["Content-Type"], "application/pdf")
            self.assertTrue(pdf.content.startswith(b"%PDF"))
            self.assertIn("attachment", pdf["Content-Disposition"])
            xlsx = self.client.get(self._url(tipo, "xlsx", obj), {"matriz": self.a.pk})
            self.assertEqual(xlsx.status_code, 200)
            self.assertIn("spreadsheetml.sheet", xlsx["Content-Type"])
            workbook = load_workbook(BytesIO(xlsx.content), read_only=True)
            self.assertTrue(workbook.sheetnames)
            workbook.close()