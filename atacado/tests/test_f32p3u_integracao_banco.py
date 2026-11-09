"""F32P3U: exercita a consolidacao efetiva usando banco de testes isolado."""
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from atacado.tests.test_f32j_ciclo_operacional import F32JCicloOperacionalTests
from atacado.integracao_transacional_pdv import consolidar_pedido_atacado_pdv
from atacado.models import StatusPedidoAtacado
from estoque.models import ReservaEstoque, SaldoEstoque
from estoque.choices import StatusReservaEstoque
from pdv.models import Caixa, SessaoCaixa, FormaPagamento, Venda
from pdv.choices import StatusOperacaoVenda, ModalidadeComercial

class F32P3UIntegracaoBancoTests(TestCase):
    setUp = F32JCicloOperacionalTests.setUp
    pedido = F32JCicloOperacionalTests.pedido

    def preparar(self):
        usuario = get_user_model().objects.create_user(
            username='f32p3u_operador', password='teste-f32p3u', matriz=self.matriz,
            is_active=True,
        )
        usuario.lojas.add(self.loja)
        pedido = self.pedido()
        # F32P3V: fixture F32J nao atribui os totais comerciais.
        # Quatro unidades a R$ 10,00 = R$ 40,00; sem frete ou descontos.
        pedido.total = Decimal('40.00')
        pedido.subtotal_produtos = Decimal('40.00')
        pedido.save(update_fields=['total', 'subtotal_produtos'])
        orcamento = pedido.orcamento_origem
        orcamento.total = Decimal('40.00')
        orcamento.subtotal_produtos = Decimal('40.00')
        orcamento.save(update_fields=['total', 'subtotal_produtos'])
        pedido.vendedor = usuario
        pedido.save(update_fields=['vendedor'])
        caixa = Caixa.objects.create(matriz=self.matriz, loja=self.loja, nome='Caixa F32P3U', codigo='F32P3U')
        sessao = SessaoCaixa.objects.create(caixa=caixa, operador_abertura=usuario)
        forma = FormaPagamento.objects.create(
            matriz=self.matriz, nome='Dinheiro F32P3U', codigo='F32P3U-DIN',
            movimenta_caixa=True, permite_troco=False,
        )
        pagamentos = [{'forma_pagamento_id': forma.pk, 'valor': str(pedido.total), 'parcelas': 1}]
        return pedido, sessao, usuario, pagamentos

    def test_consolidacao_valida_e_idempotente(self):
        pedido, sessao, operador, pagamentos = self.preparar()
        venda = consolidar_pedido_atacado_pdv(
            pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        pedido.refresh_from_db()
        self.saldo.refresh_from_db()
        self.assertEqual(pedido.venda_pdv_id, venda.pk)
        self.assertEqual(pedido.status, StatusPedidoAtacado.FINALIZADO)
        self.assertEqual(venda.status, StatusOperacaoVenda.FINALIZADA)
        self.assertEqual(venda.modalidade, ModalidadeComercial.ATACADO)
        self.assertEqual(venda.sessao_caixa_id, sessao.pk)
        self.assertEqual(venda.total, pedido.total)
        self.assertEqual(ReservaEstoque.objects.count(), 1)
        self.assertEqual(ReservaEstoque.objects.get().status, StatusReservaEstoque.CONFIRMADA)
        self.assertEqual(self.saldo.quantidade_atual, Decimal('6.000'))
        segunda = consolidar_pedido_atacado_pdv(
            pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        self.assertEqual(segunda.pk, venda.pk)
        self.assertEqual(Venda.objects.count(), 1)
        self.assertEqual(ReservaEstoque.objects.count(), 1)
        self.saldo.refresh_from_db()
        self.assertEqual(self.saldo.quantidade_atual, Decimal('6.000'))

    def test_rollback_apos_confirmacao_de_reserva(self):
        pedido, sessao, operador, pagamentos = self.preparar()
        with patch('atacado.integracao_transacional_pdv.registrar_movimentacao_caixa_venda',
                   side_effect=RuntimeError('F32P3U: falha controlada depois da reserva')):
            with self.assertRaisesRegex(RuntimeError, 'falha controlada'):
                consolidar_pedido_atacado_pdv(
                    pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        pedido.refresh_from_db()
        self.saldo.refresh_from_db()
        self.assertIsNone(pedido.venda_pdv_id)
        self.assertEqual(pedido.status, StatusPedidoAtacado.GERADO)
        self.assertEqual(Venda.objects.count(), 0)
        self.assertEqual(ReservaEstoque.objects.count(), 1)
        self.assertEqual(ReservaEstoque.objects.get().status, StatusReservaEstoque.ATIVA)
        self.assertEqual(self.saldo.quantidade_atual, Decimal('10.000'))