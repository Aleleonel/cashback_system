"""F32-RET09: cobertura de vendedor, recebiveis e ACL; somente banco de testes."""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.services import usuario_tem_permissao
from accounts.permissions import PERMISSAO_FINANCEIRO_GERENCIAR, PERMISSAO_FINANCEIRO_BAIXAR
from atacado.tests.test_f32p3y_caixa_financeiro_comissoes import F32P3YCaixaFinanceiroComissoesTests
from atacado.integracao_transacional_pdv import consolidar_pedido_atacado_pdv
from configuracoes.services_comissoes import orquestrar_comissoes_competencia
from financeiro.models import TituloFinanceiro
from pdv.models import FormaPagamento


class F32RET09RegrasNegocioTests(F32P3YCaixaFinanceiroComissoesTests):
    def test_vendedor_diferente_do_operador_recebe_comissao(self):
        pedido, sessao, operador, pagamentos = self.preparar()
        vendedor = get_user_model().objects.create_user(
            username='f32ret09_vendedor', password='teste-f32ret09', matriz=self.matriz,
            is_active=True,
        )
        vendedor.lojas.add(self.loja)
        pedido.vendedor = vendedor
        pedido.save(update_fields=['vendedor'])
        venda = consolidar_pedido_atacado_pdv(
            pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        self.assertEqual(venda.vendedor_id, vendedor.pk)
        self.assertEqual(venda.operador_id, operador.pk)
        resultado = orquestrar_comissoes_competencia(
            vendas_validas=[venda],
            metas=[{'valor_meta': Decimal('1.00'), 'percentual': Decimal('5.00')}],
            exigir_minimo_individual=False, minimo_individual=Decimal('0.00'))
        self.assertEqual(resultado.comissoes[vendedor.pk], Decimal('2.00'))
        self.assertNotIn(operador.pk, resultado.comissoes)

    def test_parcelas_geradas_com_valor_total_e_vencimentos_mensais(self):
        pedido, sessao, operador, _ = self.preparar()
        forma = FormaPagamento.objects.create(
            matriz=self.matriz, nome='Prazo F32RET09', codigo='F32RET09-PRAZO',
            movimenta_caixa=False, gera_contas_receber=True, gera_cashback=False,
            permite_parcelamento=True, maximo_parcelas=2)
        pagamentos = [{'forma_pagamento_id': forma.pk, 'valor': '40.00', 'parcelas': 2}]
        venda = consolidar_pedido_atacado_pdv(
            pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        titulos = TituloFinanceiro.objects.filter(
            origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            matriz=self.matriz, loja=self.loja)
        self.assertEqual(titulos.count(), 1)
        parcelas = list(titulos.get().parcelas.order_by('numero'))
        self.assertEqual(len(parcelas), 2)
        self.assertEqual([p.valor_original for p in parcelas], [Decimal('20.00'), Decimal('20.00')])
        self.assertLess(parcelas[0].vencimento, parcelas[1].vencimento)
        self.assertGreater(parcelas[0].vencimento, venda.finalizada_em.date())
        consolidar_pedido_atacado_pdv(
            pedido=pedido, sessao_caixa=sessao, operador=operador, pagamentos=pagamentos)
        self.assertEqual(TituloFinanceiro.objects.filter(
            origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            matriz=self.matriz, loja=self.loja).count(), 1)

    def test_operador_nao_recebe_financeiro_administrativo_automaticamente(self):
        _, _, operador, _ = self.preparar()
        operador.perfil = 'operador'
        operador.save(update_fields=['perfil'])
        self.assertFalse(usuario_tem_permissao(operador, PERMISSAO_FINANCEIRO_GERENCIAR))
        self.assertFalse(usuario_tem_permissao(operador, PERMISSAO_FINANCEIRO_BAIXAR))