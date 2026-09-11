from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from pdv.models import Venda


class Cliente360LinkDetalheCompraTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Link Detalhe")
        self.loja_origem = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Origem Link",
            status=StatusOperacional.ATIVA,
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja B Link",
            status=StatusOperacional.ATIVA,
        )

        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_link_detalhe",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja_origem)

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Cliente Link Detalhe",
            cpf="52998224725",
            tipo_pessoa="PF",
        )

        self.venda = Venda.objects.create(
            matriz=self.matriz,
            loja=self.loja_b,
            cliente=self.cliente,
            operador=self.usuario,
            subtotal=Decimal("175.00"),
            total=Decimal("175.00"),
            status="finalizada",
        )

        self.client.force_login(self.usuario)
        self.extrato_url = reverse(
            "clientes:extrato_cliente",
            args=[self.cliente.id],
        )
        self.detalhe_url = reverse(
            "clientes:detalhe_compra_cliente",
            args=[self.cliente.id, self.venda.id],
        )

    def test_aba_compras_exibe_bloco_proprio_de_listagem(self):
        response = self.client.get(
            self.extrato_url,
            {"secao": "compras"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'data-cliente360-compras="lista"',
            html=False,
        )

    def test_aba_compras_exibe_link_ver_detalhes_para_venda_finalizada(self):
        response = self.client.get(
            self.extrato_url,
            {"secao": "compras"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.detalhe_url)
        self.assertContains(response, "Ver detalhes")

    def test_link_detalhe_respeita_compra_em_outra_loja_da_mesma_matriz(self):
        self.assertEqual(self.cliente.loja_cadastro_id, self.loja_origem.id)
        self.assertEqual(self.venda.loja_id, self.loja_b.id)

        response = self.client.get(
            self.extrato_url,
            {"secao": "compras"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.loja_b.nome)
        self.assertContains(response, self.detalhe_url)