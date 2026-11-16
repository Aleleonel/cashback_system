"""F32P4H79: gaveta fisica separada de recebimentos eletronicos."""
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.models import FormaPagamento, MovimentacaoCaixa, PagamentoVenda, Venda
from pdv.services.vendas.caixa import (
    calcular_valor_movimenta_caixa, calcular_saldo_sessao_caixa,
    registrar_movimentacao_caixa_venda, registrar_movimentacao_caixa_operacional,
)
from pdv.services.vendas.fechamento import garantir_formas_pagamento_basicas
from pdv.tests.test_f2ea21_demonstrativo_caixa_db import F2EA21DemonstrativoCaixaDBTests

class F32P4H79CaixaFisicoTests(TestCase):
    setUp = F2EA21DemonstrativoCaixaDBTests.setUp

    def _forma(self, codigo, tipo, movimenta=True):
        return FormaPagamento.objects.create(
            matriz=self.matriz, codigo=codigo, nome=codigo,
            tipo=tipo, movimenta_caixa=movimenta,
        )

    def _venda(self, partes):
        total = sum((valor for _, valor in partes), Decimal('0.00'))
        venda = Venda.objects.create(
            matriz=self.matriz, loja=self.loja, sessao_caixa=self.sessao,
            operador=self.admin, vendedor=self.admin, subtotal=total, total=total,
        )
        for forma, valor in partes:
            PagamentoVenda.objects.create(venda=venda, forma_pagamento=forma, valor=valor)
        return venda

    def test_misto_somente_dinheiro_entra_na_gaveta(self):
        pix = self._forma('F32H79_PIX', TipoFormaPagamento.PIX)
        credito = self._forma('F32H79_CREDITO', TipoFormaPagamento.CARTAO_CREDITO)
        venda = self._venda([
            (self.dinheiro, Decimal('200.00')),
            (pix, Decimal('300.00')),
            (credito, Decimal('500.00')),
        ])
        self.assertEqual(calcular_valor_movimenta_caixa(venda=venda), Decimal('200.00'))
        movimento = registrar_movimentacao_caixa_venda(venda=venda, operador=self.admin)
        self.assertEqual(movimento.valor, Decimal('200.00'))
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao), Decimal('300.00'))
        self.assertEqual(registrar_movimentacao_caixa_venda(venda=venda, operador=self.admin).pk, movimento.pk)
        self.assertEqual(MovimentacaoCaixa.objects.filter(venda=venda, tipo=TipoMovimentacaoCaixa.VENDA).count(), 1)
        with self.assertRaises(ValidationError):
            registrar_movimentacao_caixa_operacional(
                sessao_caixa=self.sessao, tipo=TipoMovimentacaoCaixa.SANGRIA,
                valor=Decimal('300.01'), operador=self.admin,
            )

    def test_pix_cartoes_nao_geram_movimento_fisico(self):
        for tipo in (TipoFormaPagamento.PIX, TipoFormaPagamento.CARTAO_CREDITO, TipoFormaPagamento.CARTAO_DEBITO):
            with self.subTest(tipo=tipo):
                forma = self._forma('F32H79_' + tipo, tipo, movimenta=True)
                venda = self._venda([(forma, Decimal('50.00'))])
                self.assertEqual(calcular_valor_movimenta_caixa(venda=venda), Decimal('0.00'))
                self.assertIsNone(registrar_movimentacao_caixa_venda(venda=venda, operador=self.admin))
                self.assertFalse(MovimentacaoCaixa.objects.filter(venda=venda, tipo=TipoMovimentacaoCaixa.VENDA).exists())
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao), Decimal('100.00'))

    def test_dinheiro_desabilitado_nao_movimenta_por_configuracao(self):
        forma = self._forma('F32H79_DIN_OFF', TipoFormaPagamento.DINHEIRO, movimenta=False)
        venda = self._venda([(forma, Decimal('50.00'))])
        self.assertEqual(calcular_valor_movimenta_caixa(venda=venda), Decimal('0.00'))

    def test_formas_basicas_novas_somente_dinheiro_movimenta(self):
        garantir_formas_pagamento_basicas(matriz=self.matriz)
        for codigo, esperado in [('DINHEIRO', True), ('PIX', False), ('CREDITO', False), ('DEBITO', False)]:
            with self.subTest(codigo=codigo):
                self.assertEqual(FormaPagamento.objects.get(matriz=self.matriz, codigo=codigo).movimenta_caixa, esperado)