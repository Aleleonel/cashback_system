from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from cashback.models import LancamentoCashback
from beneficios.selectors import get_resumo_beneficios
from beneficios.services import (
    calcular_desconto_voucher,
    get_melhor_voucher,
    simular_compra,
)
from clientes.models import Cliente
from empresas.models import Loja, Matriz
from vouchers.models import Voucher


class MotorBeneficiosTest(TestCase):

    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Benefícios'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Benefícios'
        )

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome='Cliente Benefícios',
            cpf='12345678900'
        )

        self.hoje = timezone.localdate()

    def test_resumo_beneficios_com_cashback_e_voucher(self):
        LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_compra=Decimal('100.00'),
            percentual_cashback=Decimal('10.00'),
            valor_cashback=Decimal('10.00'),
            valor_utilizado=Decimal('0.00'),
            data_liberacao=self.hoje,
            data_expiracao=self.hoje + timedelta(days=10)
        )

        Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-TESTE-01',
            nome='Voucher Teste',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('20.00'),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=10),
            limite_utilizacao=1
        )

        resumo = get_resumo_beneficios(
            matriz=self.matriz,
            cliente=self.cliente
        )

        self.assertEqual(
            resumo['cashback_disponivel'],
            Decimal('10.00')
        )

        self.assertEqual(
            resumo['total_vouchers_valor_fixo'],
            Decimal('20.00')
        )

        self.assertEqual(
            resumo['total_beneficios_estimado'],
            Decimal('30.00')
        )

    def test_calcular_desconto_voucher_valor_fixo(self):
        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-TESTE-02',
            nome='Voucher Valor Fixo',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('25.00'),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=10),
            limite_utilizacao=1
        )

        desconto = calcular_desconto_voucher(
            voucher=voucher,
            valor_compra=Decimal('100.00')
        )

        self.assertEqual(
            desconto,
            Decimal('25.00')
        )

    def test_calcular_desconto_voucher_percentual(self):
        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-TESTE-03',
            nome='Voucher Percentual',
            tipo=Voucher.Tipo.PERCENTUAL,
            percentual=Decimal('10.00'),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=10),
            limite_utilizacao=1
        )

        desconto = calcular_desconto_voucher(
            voucher=voucher,
            valor_compra=Decimal('200.00')
        )

        self.assertEqual(
            desconto,
            Decimal('20.00')
        )

    def test_simular_compra_com_cashback_e_voucher(self):
        LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_compra=Decimal('100.00'),
            percentual_cashback=Decimal('10.00'),
            valor_cashback=Decimal('10.00'),
            valor_utilizado=Decimal('0.00'),
            data_liberacao=self.hoje,
            data_expiracao=self.hoje + timedelta(days=10)
        )

        voucher = Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-TESTE-04',
            nome='Voucher Compra',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('20.00'),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=10),
            limite_utilizacao=1
        )

        simulacao = simular_compra(
            matriz=self.matriz,
            cliente=self.cliente,
            valor_compra=Decimal('100.00'),
            voucher=voucher,
            valor_cashback_usado=Decimal('10.00')
        )

        self.assertEqual(simulacao['desconto_voucher'], Decimal('20.00'))
        self.assertEqual(simulacao['cashback_usado'], Decimal('10.00'))
        self.assertEqual(simulacao['total_desconto'], Decimal('30.00'))
        self.assertEqual(simulacao['valor_final'], Decimal('70.00'))

    def test_melhor_voucher(self):
        Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-TESTE-05',
            nome='Voucher Menor',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('10.00'),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=10),
            limite_utilizacao=1
        )

        voucher_maior = Voucher.objects.create(
            matriz=self.matriz,
            codigo='VCH-TESTE-06',
            nome='Voucher Maior',
            tipo=Voucher.Tipo.VALOR_FIXO,
            valor=Decimal('30.00'),
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=10),
            limite_utilizacao=1
        )

        melhor = get_melhor_voucher(
            matriz=self.matriz,
            cliente=self.cliente,
            valor_compra=Decimal('100.00')
        )

        self.assertEqual(melhor, voucher_maior)