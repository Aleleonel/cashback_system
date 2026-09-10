from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from core.choices import StatusOperacional


class Cliente360UITests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz UI 360")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja UI 360", status=StatusOperacional.ATIVA)
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="usuario_ui_360",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )
        self.usuario.lojas.add(self.loja)
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome="Cliente UI 360",
            cpf="52998224725",
        )
        self.client.force_login(self.usuario)

    def test_extrato_evolui_para_cliente_360_e_expoe_contexto(self):
        response = self.client.get(
            reverse("clientes:extrato_cliente", args=[self.cliente.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("cliente_360", response.context)
        dados = response.context["cliente_360"]
        self.assertIn("total_gasto", dados)
        self.assertIn("quantidade_compras", dados)
        self.assertIn("ticket_medio", dados)
        self.assertIn("ultima_compra", dados)
        self.assertIn("historico_vendas", dados)
        self.assertIn("cashback", dados)
        self.assertIn("vouchers", dados)

    def test_template_exibe_identidade_metricas_historico_e_beneficios(self):
        response = self.client.get(
            reverse("clientes:extrato_cliente", args=[self.cliente.id])
        )
        self.assertContains(response, "Cliente 360")
        self.assertContains(response, "Total gasto")
        self.assertContains(response, "Quantidade de compras")
        self.assertContains(response, "Ticket médio")
        self.assertContains(response, "Histórico de compras")
        self.assertContains(response, "Cashback")
        self.assertContains(response, "Vouchers")

    def test_extrato_de_cliente_de_outra_matriz_permanece_inacessivel(self):
        outra = Matriz.objects.create(nome="Outra Matriz UI 360")
        outra_loja = Loja.objects.create(matriz=outra, nome="Outra Loja UI 360")
        outro_cliente = Cliente.objects.create(
            matriz=outra,
            loja_cadastro=outra_loja,
            nome="Cliente Outra Matriz UI 360",
            cpf="11144477735",
        )
        response = self.client.get(
            reverse("clientes:extrato_cliente", args=[outro_cliente.id])
        )
        self.assertEqual(response.status_code, 404)
    def test_pj_exibe_cnpj_e_razao_social_sem_rotulo_cpf(self):
        cliente_pj = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            tipo_pessoa="PJ",
            nome="Empresa Teste LTDA",
            razao_social="Empresa Teste LTDA",
            nome_fantasia="Empresa Teste",
            cnpj="11222333000181",
            cnpj_normalizado="11222333000181",
            telefone="11999999999",
            ativo=True,
        )
        response = self.client.get(reverse("clientes:extrato_cliente", args=[cliente_pj.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CNPJ")
        self.assertContains(response, "Empresa Teste LTDA")
        self.assertNotContains(response, "<strong>CPF:</strong>", html=True)

    def test_loja_cadastro_e_rotulada_como_origem_do_cadastro(self):
        response = self.client.get(reverse("clientes:extrato_cliente", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Loja de origem do cadastro")

    def test_ultima_compra_cashback_tem_rotulo_especifico(self):
        response = self.client.get(reverse("clientes:extrato_cliente", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Última compra com cashback")

    def test_ui_historico_exibe_compras_de_duas_lojas_da_mesma_matriz(self):
        from decimal import Decimal
        from pdv.models import Venda

        loja_b = Loja.objects.create(matriz=self.matriz, nome="Loja B UI 360", status=StatusOperacional.ATIVA)
        Venda.objects.create(matriz=self.matriz, loja=self.loja, cliente=self.cliente, operador=self.usuario, subtotal=Decimal("100.00"), total=Decimal("100.00"), status="finalizada")
        Venda.objects.create(matriz=self.matriz, loja=loja_b, cliente=self.cliente, operador=self.usuario, subtotal=Decimal("200.00"), total=Decimal("200.00"), status="finalizada")
        response = self.client.get(reverse("clientes:extrato_cliente", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.loja.nome)
        self.assertContains(response, "Loja B UI 360")
        self.assertContains(response, "R$ 100,00")
        self.assertContains(response, "R$ 200,00")

    def test_ui_exibe_uso_voucher_em_loja_distinta_da_origem(self):
        from decimal import Decimal
        from django.utils import timezone
        from vouchers.models import UsoVoucher, Voucher

        loja_b = Loja.objects.create(matriz=self.matriz, nome="Loja B Voucher UI 360", status=StatusOperacional.ATIVA)
        tipo = Voucher._meta.get_field("tipo").choices[0][0]
        voucher = Voucher.objects.create(matriz=self.matriz, cliente=None, codigo="UIUSO360", nome="Voucher Uso UI 360", descricao="Teste uso voucher UI", tipo=tipo, valor=Decimal("10.00"), percentual=None, data_fim=timezone.localdate())
        UsoVoucher.objects.create(matriz=self.matriz, voucher=voucher, compra=None, cliente=self.cliente, loja=loja_b, usuario=self.usuario, valor_compra=Decimal("100.00"), valor_desconto=Decimal("10.00"), observacao="Uso voucher UI loja B")
        response = self.client.get(reverse("clientes:extrato_cliente", args=[self.cliente.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voucher utilizado")
        self.assertContains(response, "UIUSO360")
        self.assertContains(response, "Loja B Voucher UI 360")
        self.assertContains(response, "R$ 10,00")
