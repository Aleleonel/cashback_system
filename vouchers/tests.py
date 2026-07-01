from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from clientes.models import Cliente
from empresas.models import Loja, Matriz
from vouchers.models import UsoVoucher, Voucher, VoucherLoja


class VoucherModelTest(TestCase):

    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Teste'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Teste'
        )

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome='Cliente Teste',
            cpf='12345678900'
        )

        self.User = get_user_model()

        self.usuario = self.User.objects.create_user(
            username='usuario_voucher',
            password='123456',
            matriz=self.matriz
        )

        self.usuario.lojas.add(self.loja)

    def test_voucher_valor_fixo_disponivel_para_uso(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE1',
            nome='Voucher Teste',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=5
        )

        self.assertTrue(voucher.disponivel_para_uso)

    def test_voucher_expirado_nao_disponivel(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE2',
            nome='Voucher Expirado',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=hoje - timedelta(days=10),
            data_fim=hoje - timedelta(days=1),
            limite_utilizacao=5
        )

        self.assertTrue(voucher.esta_expirado)
        self.assertFalse(voucher.disponivel_para_uso)

    def test_voucher_esgotado_nao_disponivel(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE3',
            nome='Voucher Esgotado',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=1,
            total_utilizado=1
        )

        self.assertTrue(voucher.esta_esgotado)
        self.assertFalse(voucher.disponivel_para_uso)

    def test_voucher_loja_relacionamento(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE4',
            nome='Voucher Loja',
            tipo=Voucher.Tipo.PERCENTUAL,
            percentual=Decimal('10.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=3
        )

        relacao = VoucherLoja.objects.create(
            voucher=voucher,
            loja=self.loja
        )

        self.assertEqual(relacao.voucher, voucher)
        self.assertEqual(relacao.loja, self.loja)

    def test_uso_voucher(self):
        hoje = timezone.localdate()

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='PROMO-TESTE5',
            nome='Voucher Uso',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('15.00'),
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=10),
            limite_utilizacao=2
        )

        uso = UsoVoucher.objects.create(
            matriz=self.matriz,
            voucher=voucher,
            cliente=self.cliente,
            loja=self.loja,
            usuario=self.usuario,
            valor_compra=Decimal('100.00'),
            valor_desconto=Decimal('15.00')
        )

        self.assertEqual(uso.voucher, voucher)
        self.assertEqual(uso.cliente, self.cliente)
        self.assertEqual(uso.valor_desconto, Decimal('15.00'))