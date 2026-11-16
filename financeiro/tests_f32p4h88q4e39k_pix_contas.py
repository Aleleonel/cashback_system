from decimal import Decimal
from django.test import TestCase
from accounts.models import PermissaoUsuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR
from empresas.models import Loja
from financeiro.models import ContaFinanceira, TituloFinanceiro, BaixaFinanceira
from financeiro.tests_f32p4h88q4e39f_pagamento_imediato import PagamentoImediatoF32Tests
from pdv.models import FormaPagamento, MovimentacaoCaixa
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa


class PagamentoImediatoPixEscopoF32Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        PagamentoImediatoF32Tests.setUpTestData.__func__(cls)
        cls.pix = FormaPagamento.objects.create(
            matriz=cls.matriz, nome='PIX F32 K', codigo='PIX_F32_K',
            tipo=TipoFormaPagamento.PIX, movimenta_caixa=False, ativa=True,
        )
        cls.conta = ContaFinanceira.objects.create(
            matriz=cls.matriz, loja=cls.loja, nome='PIX Loja F32 K',
            tipo=ContaFinanceira.Tipo.CONTA_CORRENTE, ativo=True,
        )

    payload = PagamentoImediatoF32Tests.payload
    url = PagamentoImediatoF32Tests.url

    def setUp(self):
        PermissaoUsuario.objects.get_or_create(
            usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR,
        )
        self.client.force_login(self.operador)

    def pix_payload(self, **overrides):
        data = {'forma_pagamento_imediato': str(self.pix.pk), 'conta_financeira_imediata': str(self.conta.pk)}
        data.update(overrides)
        return self.payload(**data)

    def test_pix_da_loja_liquida_sem_sangria_ou_sessao(self):
        MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao).delete()
        self.sessao.delete()
        response = self.client.post(self.url(), self.pix_payload())
        self.assertEqual(response.status_code, 302, response.content[:500])
        titulo = TituloFinanceiro.objects.get(matriz=self.matriz, entidade_nome='Motoboy F32')
        self.assertEqual(titulo.status, TituloFinanceiro.Status.LIQUIDADO)
        baixa = BaixaFinanceira.objects.get(parcela__titulo=titulo, tipo=BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.valor, Decimal('15.00'))
        self.assertEqual(baixa.conta_financeira_id, self.conta.pk)
        self.assertEqual(baixa.forma_pagamento_id, self.pix.pk)
        self.assertIsNone(baixa.movimentacao_caixa_id)
        self.assertIsNone(baixa.sessao_caixa_id)
        self.assertFalse(MovimentacaoCaixa.objects.filter(tipo=TipoMovimentacaoCaixa.SANGRIA).exists())

    def test_pix_sem_conta_nao_cria_titulo(self):
        response = self.client.post(self.url(), self.pix_payload(conta_financeira_imediata=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())
        self.assertFalse(BaixaFinanceira.objects.filter(parcela__titulo__matriz=self.matriz).exists())

    def test_pix_conta_outra_loja_rejeitada(self):
        outra_loja = Loja.objects.create(matriz=self.matriz, nome='Outra Loja F32 K')
        outra_conta = ContaFinanceira.objects.create(
            matriz=self.matriz, loja=outra_loja, nome='PIX Outra Loja F32 K',
            tipo=ContaFinanceira.Tipo.CONTA_CORRENTE, ativo=True,
        )
        response = self.client.post(self.url(), self.pix_payload(conta_financeira_imediata=str(outra_conta.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())

    def test_operador_nao_paga_com_conta_compartilhada_da_matriz(self):
        conta_matriz = ContaFinanceira.objects.create(
            matriz=self.matriz, loja=None, nome='Conta Compartilhada F32 K',
            tipo=ContaFinanceira.Tipo.CONTA_CORRENTE, ativo=True,
        )
        get = self.client.get(self.url())
        self.assertEqual(get.status_code, 200)
        self.assertNotIn(conta_matriz.pk, list(
            get.context['form'].fields['conta_financeira_imediata'].queryset.values_list('pk', flat=True)
        ))
        response = self.client.post(self.url(), self.pix_payload(conta_financeira_imediata=str(conta_matriz.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())