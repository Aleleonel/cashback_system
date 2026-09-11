from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


class Cliente360UXExtratosTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz UX Extratos")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja UX Extratos",
            status=StatusOperacional.ATIVA,
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_ux_extratos",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente UX Extratos",
            cpf="52998224725",
        )
        self.client.force_login(self.usuario)
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])

    def test_visao_geral_e_dominio_padrao(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "extrato")
        self.assertContains(response, "Extrato")
        self.assertContains(response, "Compras")
        self.assertContains(response, "Benefícios")
        self.assertContains(response, "Vouchers")

    def test_compras_pode_ser_selecionado_por_querystring(self):
        response = self.client.get(self.url, {"secao": "compras"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "compras")
        self.assertContains(response, 'data-cliente360-secao="compras"', html=False)

    def test_beneficios_pode_ser_selecionado_por_querystring(self):
        response = self.client.get(self.url, {"secao": "beneficios"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "beneficios")
        self.assertContains(response, 'data-cliente360-secao="beneficios"', html=False)

    def test_vouchers_pode_ser_selecionado_por_querystring(self):
        response = self.client.get(self.url, {"secao": "vouchers"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "vouchers")
        self.assertContains(response, 'data-cliente360-secao="vouchers"', html=False)

    def test_secao_invalida_retorna_visao_geral(self):
        response = self.client.get(self.url, {"secao": "qualquer-coisa"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "extrato")