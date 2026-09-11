from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model

User = get_user_model()
from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


class Cliente360CarregamentoDominios195F416G26Tests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz G26", status="ativa")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja G26", status=StatusOperacional.ATIVA)
        self.user = User.objects.create_user(
            username="g26",
            password="x",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.user.lojas.add(self.loja)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente G26",
            tipo_pessoa="PF",
            ativo=True,
        )
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.pk])
        self.client.force_login(self.user)

    def _assert_aba_nao_carrega_cliente360_completo(self, secao):
        with patch("clientes.views.obter_cliente_360", side_effect=AssertionError("EAGER_CLIENTE360_PROIBIDO_NESTA_ABA")) as mocked:
            response = self.client.get(self.url, {"secao": secao})
        self.assertEqual(response.status_code, 200)
        mocked.assert_not_called()

    def test_compras_nao_carrega_cliente360_completo(self):
        self._assert_aba_nao_carrega_cliente360_completo("compras")

    def test_beneficios_nao_carrega_cliente360_completo(self):
        self._assert_aba_nao_carrega_cliente360_completo("beneficios")

    def test_vouchers_nao_carrega_cliente360_completo(self):
        self._assert_aba_nao_carrega_cliente360_completo("vouchers")

    def test_visao_geral_legada_cai_em_extrato_sem_eager(self):
        with patch("clientes.views.obter_cliente_360", side_effect=AssertionError("EAGER_CLIENTE360_PROIBIDO_NO_EXTRATO")) as mocked:
            response = self.client.get(self.url, {"secao": "visao-geral"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["dominio_ativo"], "extrato")
        mocked.assert_not_called()
