import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from cashback.models import (
    LancamentoCashback,
    UsoCashback,
)
from cashback.services.operacao import executar_venda_idempotente
from cashback.services.venda import registrar_venda
from clientes.models import Cliente
from empresas.models import Loja, Matriz


class RegistrarVendaIdempotenciaTest(TestCase):

    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz IdempotÃªncia'
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja IdempotÃªncia'
        )

        self.cliente = Cliente.objects.create(
            matriz=self.matriz,
            loja_cadastro=self.loja,
            nome='Cliente Teste IdempotÃªncia',
            cpf='12345678901',
            aceita_email=False,
            aceita_sms=False,
        )

        hoje = timezone.localdate()

        self.cashback_origem = LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            valor_compra=Decimal('100.00'),
            valor_base_cashback=Decimal('100.00'),
            percentual_cashback=Decimal('10.00'),
            valor_cashback=Decimal('20.00'),
            valor_utilizado=Decimal('0.00'),
            data_compra=hoje,
            data_liberacao=hoje,
            data_expiracao=hoje + timedelta(days=30),
            observacao='Saldo para teste de idempotÃªncia.',
        )

    def test_mesma_chave_nao_registra_venda_duas_vezes(self):
        chave_idempotencia = uuid.uuid4()

        dados_venda = {
            'matriz': self.matriz,
            'loja': self.loja,
            'usuario': None,
            'chave_idempotencia': chave_idempotencia,
            'cpf': self.cliente.cpf,
            'nome': self.cliente.nome,
            'telefone': self.cliente.telefone or '',
            'email': self.cliente.email or '',
            'data_nascimento': self.cliente.data_nascimento,
            'valor_compra': Decimal('100.00'),
            'valor_cashback_usado': Decimal('10.00'),
            'aceita_email': self.cliente.aceita_email,
            'aceita_sms': self.cliente.aceita_sms,
            'observacao': 'Compra do teste de idempotÃªncia.',
            'aplicar_voucher': False,
            'codigo_voucher': '',
        }

        primeiro_resultado = registrar_venda(**dados_venda)
        segundo_resultado = registrar_venda(**dados_venda)

        compras_da_operacao = LancamentoCashback.objects.filter(
            matriz=self.matriz,
            chave_idempotencia=chave_idempotencia,
        )

        usos_cashback = UsoCashback.objects.filter(
            matriz=self.matriz,
            cliente=self.cliente,
        )

        self.cashback_origem.refresh_from_db()

        self.assertFalse(primeiro_resultado['duplicada'])
        self.assertTrue(segundo_resultado['duplicada'])

        self.assertEqual(
            primeiro_resultado['compra'].id,
            segundo_resultado['compra'].id,
        )

        self.assertEqual(compras_da_operacao.count(), 1)
        self.assertEqual(usos_cashback.count(), 1)

        self.assertEqual(
            self.cashback_origem.valor_utilizado,
            Decimal('10.00'),
        )

        compra = compras_da_operacao.get()

        self.assertEqual(
            compra.valor_base_cashback,
            Decimal('90.00'),
        )

    def test_orquestrador_recupera_compra_apos_integrity_error_idempotente(self):
        chave_idempotencia = uuid.uuid4()

        compra_existente = LancamentoCashback.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            cliente=self.cliente,
            chave_idempotencia=chave_idempotencia,
            valor_compra=Decimal('100.00'),
            valor_base_cashback=Decimal('100.00'),
            percentual_cashback=Decimal('10.00'),
            valor_cashback=Decimal('10.00'),
            valor_utilizado=Decimal('0.00'),
            data_compra=timezone.localdate(),
            data_liberacao=timezone.localdate(),
            data_expiracao=timezone.localdate() + timedelta(days=30),
            observacao='Compra concorrente jÃ¡ confirmada.',
        )

        with patch(
            'cashback.services.operacao.registrar_venda',
            side_effect=IntegrityError('chave duplicada'),
        ):
            resultado = executar_venda_idempotente(
                matriz=self.matriz,
                loja=self.loja,
                usuario=None,
                chave_idempotencia=chave_idempotencia,
                cpf=self.cliente.cpf,
                nome=self.cliente.nome,
                valor_compra=Decimal('100.00'),
            )

        self.assertTrue(resultado['duplicada'])
        self.assertEqual(
            resultado['compra'].id,
            compra_existente.id,
        )
        self.assertEqual(
            resultado['cliente'].id,
            self.cliente.id,
        )

    def test_orquestrador_relanca_integrity_error_nao_idempotente(self):
        chave_idempotencia = uuid.uuid4()

        with patch(
            'cashback.services.operacao.registrar_venda',
            side_effect=IntegrityError('erro de integridade nÃ£o relacionado'),
        ):
            with self.assertRaises(IntegrityError):
                executar_venda_idempotente(
                    matriz=self.matriz,
                    loja=self.loja,
                    usuario=None,
                    chave_idempotencia=chave_idempotencia,
                    cpf=self.cliente.cpf,
                    nome=self.cliente.nome,
                    valor_compra=Decimal('100.00'),
                )
