from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from pdv.models import Venda


class Cliente360DetalheCompraTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Detalhe Compra")
        self.loja_origem = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Origem Detalhe",
            status=StatusOperacional.ATIVA,
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja B Detalhe",
            status=StatusOperacional.ATIVA,
        )

        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_detalhe_compra",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        # Deliberadamente apenas a loja de origem:
        # o detalhe Cliente 360 deve continuar no escopo da matriz.
        self.usuario.lojas.add(self.loja_origem)

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Cliente Detalhe Compra",
            cpf="52998224725",
            tipo_pessoa="PF",
        )
        self.outro_cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Outro Cliente Detalhe",
            cpf="11144477735",
            tipo_pessoa="PF",
        )

        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja_b,
            cliente=self.cliente,
            operador=self.usuario,
            subtotal=Decimal("150.00"),
            total=Decimal("150.00"),
            status="finalizada",
        )
        self.client.force_login(self.usuario)

    def url(self, cliente, venda):
        return reverse(
            "clientes:detalhe_compra_cliente",
            args=[cliente.id, venda.id],
        )

    def test_detalhe_compra_finalizada_da_mesma_matriz_retorna_200(self):
        response = self.client.get(self.url(self.cliente, self.venda))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cliente"].id, self.cliente.id)
        self.assertEqual(response.context["venda"].id, self.venda.id)

    def test_detalhe_expoe_itens_pagamentos_e_resumo(self):
        response = self.client.get(self.url(self.cliente, self.venda))
        self.assertEqual(response.status_code, 200)
        self.assertIn("itens", response.context)
        self.assertIn("pagamentos", response.context)
        self.assertIn("resumo_pagamentos", response.context)

    def test_compra_de_loja_b_da_mesma_matriz_e_acessivel_independente_loja_cadastro(self):
        self.assertEqual(self.cliente.loja_cadastro_id, self.loja_origem.id)
        self.assertEqual(self.venda.loja_id, self.loja_b.id)
        response = self.client.get(self.url(self.cliente, self.venda))
        self.assertEqual(response.status_code, 200)

    def test_venda_de_outro_cliente_nao_pode_ser_aberta_no_cliente_atual(self):
        venda_outro = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja_origem,
            cliente=self.outro_cliente,
            operador=self.usuario,
            subtotal=Decimal("99.00"),
            total=Decimal("99.00"),
            status="finalizada",
        )
        response = self.client.get(self.url(self.cliente, venda_outro))
        self.assertEqual(response.status_code, 404)

    def test_venda_cancelada_nao_faz_parte_do_detalhe_de_compra_cliente_360(self):
        cancelada = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja_origem,
            cliente=self.cliente,
            operador=self.usuario,
            subtotal=Decimal("80.00"),
            total=Decimal("80.00"),
            status="cancelada",
        )
        response = self.client.get(self.url(self.cliente, cancelada))
        self.assertEqual(response.status_code, 404)

    def test_venda_inconsistente_de_outra_matriz_nao_vaza(self):
        outra_matriz = Matriz.objects.create(nome="Outra Matriz Detalhe")
        outra_loja = Loja.objects.create(
            matriz=outra_matriz,
            nome="Outra Loja Detalhe",
            status=StatusOperacional.ATIVA,
        )
        User = get_user_model()
        outro_operador = User.objects.create_user(
            username="outro_operador_detalhe",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=outra_matriz,
        )
        venda_inconsistente = Venda.objects.create(
            matriz=outra_matriz,
            loja=outra_loja,
            cliente=self.cliente,
            operador=outro_operador,
            subtotal=Decimal("999.00"),
            total=Decimal("999.00"),
            status="finalizada",
        )
        response = self.client.get(
            self.url(self.cliente, venda_inconsistente)
        )
        self.assertEqual(response.status_code, 404)