from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from cashback.models import LancamentoCashback, UsoCashback
from clientes.models import Cliente
from clientes.selectors import obter_cliente_360
from empresas.models import Loja, Matriz
from vouchers.models import UsoVoucher, Voucher


class Cliente360BeneficiosTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Beneficios 360")
        self.loja_origem = Loja.objects.create(matriz=self.matriz, nome="Loja Origem")
        self.loja_b = Loja.objects.create(matriz=self.matriz, nome="Loja B")
        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja_origem,
            nome="Cliente Beneficios 360",
            cpf="52998224725",
            tipo_pessoa="PF",
        )

        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="operador_beneficios_360",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            matriz=self.matriz,
        )

    def criar_lancamento(self, *, matriz=None, loja=None, valor="20.00"):
        hoje = timezone.localdate()
        return LancamentoCashback.objects.create(
            matriz=matriz or self.matriz,
            loja=loja or self.loja_b,
            cliente=self.cliente,
            valor_compra=Decimal("200.00"),
            valor_base_cashback=Decimal("200.00"),
            percentual_cashback=Decimal("10.00"),
            valor_cashback=Decimal(valor),
            valor_utilizado=Decimal("0.00"),
            data_compra=hoje,
            data_liberacao=hoje - timedelta(days=1),
            data_expiracao=hoje + timedelta(days=30),
        )

    def criar_voucher(self, *, matriz=None, cliente=None, codigo="V360"):
        campo_tipo = Voucher._meta.get_field("tipo")
        tipo = campo_tipo.choices[0][0]
        return Voucher.objects.create(
            matriz=matriz or self.matriz,
            cliente=cliente,
            codigo=codigo,
            nome="Voucher 360",
            descricao="Voucher de teste Cliente 360",
            tipo=tipo,
            valor=Decimal("10.00"),
            percentual=None,
            data_fim=timezone.localdate() + timedelta(days=30),
        )

    def test_cashback_da_loja_b_aparece_mesmo_cliente_cadastrado_na_loja_origem(self):
        self.criar_lancamento(loja=self.loja_b, valor="20.00")
        UsoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja_b,
            cliente=self.cliente,
            valor_usado=Decimal("5.00"),
            data_uso=timezone.localdate(),
            observacao="Uso loja B",
        )

        dados = obter_cliente_360(self.cliente)

        self.assertIn("cashback", dados)
        self.assertEqual(dados["cashback"]["saldo_disponivel"], Decimal("20.00"))
        self.assertEqual(dados["cashback"]["resumo"]["total_gerado"], Decimal("20.00"))
        self.assertEqual(dados["cashback"]["resumo"]["total_utilizado"], Decimal("5.00"))
        lojas = {m["loja"].id for m in dados["cashback"]["movimentacoes"] if m["loja"]}
        self.assertIn(self.loja_b.id, lojas)

    def test_voucher_global_e_uso_na_loja_b_aparecem_sem_restricao_por_loja_cadastro(self):
        voucher_global = self.criar_voucher(cliente=None, codigo="GLOBAL360")
        UsoVoucher.objects.create(
            matriz=self.matriz,
            voucher=voucher_global,
            compra=None,
            cliente=self.cliente,
            loja=self.loja_b,
            usuario=self.usuario,
            valor_compra=Decimal("100.00"),
            valor_desconto=Decimal("10.00"),
            observacao="Uso voucher loja B",
        )

        dados = obter_cliente_360(self.cliente)

        self.assertIn("vouchers", dados)
        ids_vouchers = {v.id for v in dados["vouchers"]["lista"]}
        self.assertIn(voucher_global.id, ids_vouchers)
        usos = list(dados["vouchers"]["usos"])
        self.assertEqual(len(usos), 1)
        self.assertEqual(usos[0].loja_id, self.loja_b.id)

    def test_beneficios_de_outra_matriz_nao_vazam_para_cliente_360(self):
        outra_matriz = Matriz.objects.create(nome="Outra Matriz 360")
        outra_loja = Loja.objects.create(matriz=outra_matriz, nome="Outra Loja")
        self.criar_lancamento(matriz=outra_matriz, loja=outra_loja, valor="99.00")
        voucher_outra = self.criar_voucher(
            matriz=outra_matriz,
            cliente=self.cliente,
            codigo="OUTRA360",
        )

        dados = obter_cliente_360(self.cliente)

        self.assertIn("cashback", dados)
        self.assertEqual(dados["cashback"]["saldo_disponivel"], Decimal("0.00"))
        self.assertIn("vouchers", dados)
        ids_vouchers = {v.id for v in dados["vouchers"]["lista"]}
        self.assertNotIn(voucher_outra.id, ids_vouchers)


