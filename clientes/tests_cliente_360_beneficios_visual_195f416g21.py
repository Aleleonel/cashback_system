from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from clientes.models import Cliente
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz


class Cliente360BeneficiosVisual195F416G21Tests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz G21")
        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja G21",
            status=StatusOperacional.ATIVA,
        )
        self.usuario = Usuario.objects.create_user(
            username="usuario_g21",
            password="senha-g21",
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente G21",
            cpf="52998224725",
            telefone="11999999999",
        )
        self.client.force_login(self.usuario)
        self.url = reverse("clientes:extrato_cliente", args=[self.cliente.id])

    def get_beneficios(self):
        return self.client.get(self.url, {"secao": "beneficios"})

    def test_exibe_secao_dedicada_de_beneficios(self):
        response = self.get_beneficios()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-cliente360-beneficios="lista"')

    def test_exibe_formulario_get_com_filtros_de_data(self):
        response = self.get_beneficios()
        self.assertContains(response, 'name="secao" value="beneficios"')
        self.assertContains(response, 'name="data_inicio"')
        self.assertContains(response, 'name="data_fim"')

    def test_exibe_cards_resumo_cashback(self):
        response = self.get_beneficios()
        self.assertContains(response, "Saldo disponível")
        self.assertContains(response, "Total gerado")
        self.assertContains(response, "Total utilizado")

    def test_exibe_estrutura_de_tabela_de_movimentacoes(self):
        response = self.get_beneficios()
        self.assertContains(response, "Data")
        self.assertContains(response, "Tipo")
        self.assertContains(response, "Loja")
        self.assertContains(response, "Descrição")
        self.assertContains(response, "Valor")

    def test_exibe_estado_vazio_especifico_sem_movimentacoes(self):
        response = self.get_beneficios()
        self.assertContains(response, "Nenhuma movimentação de cashback encontrada")