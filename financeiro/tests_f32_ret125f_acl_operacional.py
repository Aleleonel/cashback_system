"""RET125F: contratos comportamentais da permissao operacional isolada."""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from accounts.permissions import (
    PERMISSAO_FINANCEIRO_BAIXAR,
    PERMISSAO_FINANCEIRO_LANCAR_DESPESA,
    PERMISSAO_FINANCEIRO_PAGAR_DESPESA_OPERACIONAL,
    PERMISSAO_FINANCEIRO_VISUALIZAR,
)
from empresas.models import Loja
from financeiro.models import TituloFinanceiro, BaixaFinanceira, ContaFinanceira
from financeiro.tests_f32p4h88q4e39f_pagamento_imediato import PagamentoImediatoF32Tests
from pdv.models import FormaPagamento, MovimentacaoCaixa
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa


class ACLDespesaOperacionalRET125F(TestCase):
    @classmethod
    def setUpTestData(cls):
        PagamentoImediatoF32Tests.setUpTestData.__func__(cls)
        cls.pix = FormaPagamento.objects.create(
            matriz=cls.matriz, nome='PIX RET125F', codigo='PIX_RET125F',
            tipo=TipoFormaPagamento.PIX, movimenta_caixa=False, ativa=True,
        )
        cls.conta = ContaFinanceira.objects.create(
            matriz=cls.matriz, loja=cls.loja, nome='Conta RET125F',
            tipo=ContaFinanceira.Tipo.CONTA_CORRENTE, ativo=True,
        )

    payload = PagamentoImediatoF32Tests.payload
    url = PagamentoImediatoF32Tests.url

    def setUp(self):
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FINANCEIRO_PAGAR_DESPESA_OPERACIONAL,
        )
        self.client.force_login(self.operador)

    def test_permissao_estreita_nao_concede_acesso_geral(self):
        permissoes = set(PermissaoUsuario.objects.filter(usuario=self.operador).values_list('permissao', flat=True))
        self.assertIn(PERMISSAO_FINANCEIRO_LANCAR_DESPESA, permissoes)
        self.assertIn(PERMISSAO_FINANCEIRO_PAGAR_DESPESA_OPERACIONAL, permissoes)
        self.assertNotIn(PERMISSAO_FINANCEIRO_BAIXAR, permissoes)
        self.assertNotIn(PERMISSAO_FINANCEIRO_VISUALIZAR, permissoes)
        self.assertEqual(self.client.get(reverse('financeiro:titulos')).status_code, 403)
        self.assertEqual(self.client.get(reverse('financeiro:repasse_novo')).status_code, 403)

    def test_formulario_mostra_pagamento_sem_baixa_geral(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="liquidar_agora"')
        self.assertContains(response, 'confirmacao-pagamento-imediato')
        self.assertTrue(response.context['pode_baixar'])

    def test_dinheiro_liquida_e_gera_uma_sangria(self):
        response = self.client.post(self.url(), self.payload())
        self.assertEqual(response.status_code, 302, response.content[:500])
        self.assertEqual(response.url, self.url())
        titulo = TituloFinanceiro.objects.get(matriz=self.matriz, entidade_nome='Motoboy F32')
        self.assertEqual(titulo.status, TituloFinanceiro.Status.LIQUIDADO)
        baixa = BaixaFinanceira.objects.get(parcela__titulo=titulo, tipo=BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.valor, Decimal('15.00'))
        self.assertEqual(baixa.sessao_caixa_id, self.sessao.pk)
        self.assertEqual(baixa.movimentacao_caixa.tipo, TipoMovimentacaoCaixa.SANGRIA)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao), Decimal('85.00'))

    def test_pix_sem_caixa_nao_gera_sangria(self):
        MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao).delete()
        self.sessao.delete()
        response = self.client.post(self.url(), self.payload(
            forma_pagamento_imediato=str(self.pix.pk),
            conta_financeira_imediata=str(self.conta.pk),
        ))
        self.assertEqual(response.status_code, 302, response.content[:500])
        titulo = TituloFinanceiro.objects.get(matriz=self.matriz, entidade_nome='Motoboy F32')
        baixa = BaixaFinanceira.objects.get(parcela__titulo=titulo, tipo=BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.conta_financeira_id, self.conta.pk)
        self.assertIsNone(baixa.sessao_caixa_id)
        self.assertIsNone(baixa.movimentacao_caixa_id)
        self.assertFalse(MovimentacaoCaixa.objects.filter(tipo=TipoMovimentacaoCaixa.SANGRIA).exists())

    def test_sem_permissao_lancar_nao_abre_formulario(self):
        PermissaoUsuario.objects.filter(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_LANCAR_DESPESA).delete()
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertEqual(self.client.post(self.url(), self.payload()).status_code, 403)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())

    def test_outra_loja_rejeitada(self):
        outra = Loja.objects.create(matriz=self.matriz, nome='Loja nao autorizada RET125F')
        response = self.client.post(self.url(), self.payload(loja=str(outra.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())

    def test_sem_caixa_dinheiro_reverte_titulo(self):
        MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao).delete()
        self.sessao.delete()
        response = self.client.post(self.url(), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())

    def test_idempotencia_sem_duplicar_sangria(self):
        data = self.payload()
        self.assertEqual(self.client.post(self.url(), data).status_code, 302)
        self.assertEqual(self.client.post(self.url(), data).status_code, 302)
        self.assertEqual(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').count(), 1)
        self.assertEqual(BaixaFinanceira.objects.filter(parcela__titulo__matriz=self.matriz, tipo=BaixaFinanceira.Tipo.BAIXA).count(), 1)
        self.assertEqual(MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao, tipo=TipoMovimentacaoCaixa.SANGRIA).count(), 1)
