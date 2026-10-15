from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Matriz
from accounts.permissions import PERMISSAO_RELATORIOS_DASHBOARD

class F2EA19EscopoComprasFornecedoresTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.m=Matriz.objects.create(nome="Matriz F2EA19")
        self.admin=U.objects.create_user(username="admin_f2ea19",password="x",perfil="admin_loja",matriz=self.m)
        self.op=U.objects.create_user(username="op_f2ea19",password="x",perfil="operador",matriz=self.m)
        # O projeto resolve relatorios.dashboard por perfil/servico; este teste
        # congela apenas a fronteira adicional do dominio de compras.
    def test_admin_matriz_acessa_hub_compras(self):
        self.client.force_login(self.admin)
        r=self.client.get(reverse("relatorios:compras"))
        self.assertNotEqual(r.status_code,403)

    def test_operador_nao_acessa_hub_compras(self):
        self.client.force_login(self.op)
        r=self.client.get(reverse("relatorios:compras"))
        self.assertEqual(r.status_code,403)

    def test_operador_nao_acessa_pedidos_compra(self):
        self.client.force_login(self.op)
        r=self.client.get(reverse("relatorios:compras_pedidos"))
        self.assertEqual(r.status_code,403)

    def test_operador_nao_acessa_fornecedores(self):
        self.client.force_login(self.op)
        r=self.client.get(reverse("relatorios:compras_fornecedores"))
        self.assertEqual(r.status_code,403)