from decimal import Decimal
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cashback.models import LancamentoCashback, UsoCashback
from clientes.models import Cliente
from empresas.models import Matriz, Loja
from empresas.models import StatusOperacional


class Cliente360BeneficiosValores195F416G35Tests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz G35")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja G35",
            status=StatusOperacional.ATIVA,
        )
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_g35",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente G35",
            cpf="52998224725",
            tipo_pessoa="PF",
        )
        self.client.force_login(self.usuario)
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])

    def criar_lancamento(self, valor="17.35"):
        hoje = timezone.localdate()
        obj = LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_compra=Decimal("100.00"),
            valor_base_cashback=Decimal("100.00"),
            percentual_cashback=Decimal("17.35"),
            valor_cashback=Decimal(valor),
            valor_utilizado=Decimal("0.00"),
            data_compra=hoje,
            data_liberacao=hoje - timedelta(days=1),
            data_expiracao=hoje + timedelta(days=30),
        )
        return obj

    def criar_uso(self, valor="5.25"):
        return UsoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_usado=Decimal(valor),
            observacao="Uso G35",
        )

    def get_beneficios(self):
        response = self.client.get(self.url, {"secao": "beneficios"})
        self.assertEqual(response.status_code, 200)
        return response

    def test_cards_exibem_valores_reais_sem_cliente360_eager(self):
        self.criar_lancamento("17.35")
        self.criar_uso("5.25")
        response = self.get_beneficios()
        self.assertContains(response, "17,35")
        self.assertContains(response, "5,25")

    def test_credito_exibe_entrada_real(self):
        self.criar_lancamento("17.35")
        response = self.get_beneficios()
        self.assertContains(response, "+ R$ 17,35")

    def test_debito_exibe_saida_real(self):
        self.criar_uso("5.25")
        response = self.get_beneficios()
        self.assertContains(response, "- R$ 5,25")

    def test_descricao_exibe_titulo_real_da_movimentacao(self):
        self.criar_lancamento("17.35")
        self.criar_uso("5.25")
        response = self.get_beneficios()
        self.assertContains(response, "Cashback gerado")
        self.assertContains(response, "Cashback utilizado")