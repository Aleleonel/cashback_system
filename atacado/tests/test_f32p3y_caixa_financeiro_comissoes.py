"""F32P3Y: invariantes de caixa, recebiveis e comissoes da consolidacao atacado."""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from atacado.tests.test_f32p3u_integracao_banco import F32P3UIntegracaoBancoTests
from atacado.integracao_transacional_pdv import consolidar_pedido_atacado_pdv
from configuracoes.services_comissoes import selecionar_vendas_validas_competencia, orquestrar_comissoes_competencia
from financeiro.models import TituloFinanceiro
from pdv.models import FormaPagamento, MovimentacaoCaixa, Venda
from pdv.choices import TipoMovimentacaoCaixa

class F32P3YCaixaFinanceiroComissoesTests(TestCase):
    setUp = F32P3UIntegracaoBancoTests.setUp
    preparar = F32P3UIntegracaoBancoTests.preparar
    pedido = F32P3UIntegracaoBancoTests.pedido

    def test_recebimento_imediato_movimenta_caixa_uma_vez(self):
        pedido, sessao, operador, pagamentos = self.preparar()
        venda = consolidar_pedido_atacado_pdv(pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        qs = MovimentacaoCaixa.objects.filter(venda=venda, tipo=TipoMovimentacaoCaixa.VENDA)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().sessao_caixa_id, sessao.pk)
        self.assertEqual(qs.get().valor, Decimal('40.00'))
        self.assertFalse(TituloFinanceiro.objects.filter(origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO).exists())
        consolidar_pedido_atacado_pdv(pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        self.assertEqual(qs.count(), 1)

    def test_pagamento_a_prazo_gera_recebivel_sem_movimentar_caixa(self):
        pedido, sessao, operador, _ = self.preparar()
        forma = FormaPagamento.objects.create(matriz=self.matriz, nome='Prazo F32P3Y', codigo='F32P3Y-PRAZO', movimenta_caixa=False, gera_contas_receber=True, gera_cashback=False, permite_parcelamento=True, maximo_parcelas=2)
        pagamentos = [{'forma_pagamento_id': forma.pk, 'valor': '40.00', 'parcelas': 2}]
        venda = consolidar_pedido_atacado_pdv(pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        self.assertFalse(MovimentacaoCaixa.objects.filter(venda=venda, tipo=TipoMovimentacaoCaixa.VENDA).exists())
        titulos = TituloFinanceiro.objects.filter(matriz=self.matriz, origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO)
        self.assertEqual(titulos.count(), 1)
        self.assertEqual(titulos.get().valor_original, Decimal('40.00'))
        consolidar_pedido_atacado_pdv(pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        self.assertEqual(titulos.count(), 1)

    def test_comissao_considera_total_venda_na_competencia(self):
        pedido, sessao, operador, pagamentos = self.preparar()
        venda = consolidar_pedido_atacado_pdv(pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        data = timezone.localtime(venda.finalizada_em)
        vendas = selecionar_vendas_validas_competencia(Venda.objects.all(), loja_id=self.loja.pk, ano=data.year, mes=data.month)
        self.assertEqual(list(vendas.values_list('pk', flat=True)), [venda.pk])
        resultado = orquestrar_comissoes_competencia(vendas_validas=vendas, metas=[{'valor_meta': Decimal('1.00'), 'percentual': Decimal('5.00')}], exigir_minimo_individual=False, minimo_individual=Decimal('0.00'))
        self.assertEqual(resultado.total_loja, Decimal('40.00'))
        self.assertEqual(resultado.vendas_por_vendedor[operador.pk], Decimal('40.00'))
        self.assertEqual(resultado.comissoes[operador.pk], Decimal('2.00'))