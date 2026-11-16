import uuid
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import Usuario, PermissaoUsuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR, PERMISSAO_FINANCEIRO_LANCAR_DESPESA
from empresas.models import Matriz, Loja
from financeiro.models import PlanoConta, TituloFinanceiro, BaixaFinanceira
from pdv.models import Caixa, SessaoCaixa, FormaPagamento, MovimentacaoCaixa
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa

class PagamentoImediatoF32Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome='F32 Imediato', cnpj='83838383000183')
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome='F32 Loja')
        cls.operador = Usuario.objects.create_user(username='f32_imediato', password='x', matriz=cls.matriz, perfil=Usuario.PERFIL_OPERADOR)
        cls.operador.lojas.add(cls.loja)
        PermissaoUsuario.objects.create(usuario=cls.operador, permissao=PERMISSAO_FINANCEIRO_LANCAR_DESPESA)
        cls.plano = PlanoConta.objects.create(matriz=cls.matriz, codigo='8.3', nome='Despesas F32', tipo=PlanoConta.Tipo.ANALITICA, aceita_lancamento=True, ativo=True)
        cls.dinheiro = FormaPagamento.objects.create(matriz=cls.matriz, nome='Dinheiro F32', codigo='DIN_F32', tipo=TipoFormaPagamento.DINHEIRO, movimenta_caixa=True, ativa=True)
        cls.caixa = Caixa.objects.create(matriz=cls.matriz, loja=cls.loja, nome='Caixa F32', codigo='CX_F32')
        cls.sessao = SessaoCaixa.objects.create(caixa=cls.caixa, operador_abertura=cls.operador, valor_abertura=Decimal('100.00'))
        MovimentacaoCaixa.objects.create(sessao_caixa=cls.sessao, tipo=TipoMovimentacaoCaixa.ABERTURA, valor=Decimal('100.00'), operador=cls.operador, descricao='Abertura')

    def payload(self, **kw):
        d = {'natureza': TituloFinanceiro.Natureza.PAGAR, 'loja': str(self.loja.pk),
             'plano_conta': str(self.plano.pk), 'centro_custo': '',
             'entidade_nome': 'Motoboy F32', 'documento_referencia': 'F32',
             'data_emissao': date.today().isoformat(), 'data_competencia': date.today().isoformat(),
             'data_vencimento': date.today().isoformat(), 'valor_bruto': '15.00',
             'valor_desconto': '0', 'valor_juros': '0', 'numero_parcelas': '1',
             'observacao': 'Teste imediato', 'liquidar_agora': 'on',
             'forma_pagamento_imediato': str(self.dinheiro.pk),
             'conta_financeira_imediata': '', 'chave_idempotencia': str(uuid.uuid4())}
        d.update(kw)
        return d

    def url(self):
        return reverse('financeiro:lancamento_manual')

    def test_sem_permissao_nao_exibe_e_rejeita_post(self):
        self.client.force_login(self.operador)
        get = self.client.get(self.url())
        self.assertEqual(get.status_code, 200)
        self.assertNotContains(get, 'name="liquidar_agora"')
        self.assertFalse(get.context['pode_baixar'])
        before = TituloFinanceiro.objects.filter(matriz=self.matriz).count()
        response = self.client.post(self.url(), self.payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(TituloFinanceiro.objects.filter(matriz=self.matriz).count(), before)

    def test_pagamento_dinheiro_cria_baixa_e_sangria(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR)
        self.client.force_login(self.operador)
        response = self.client.post(self.url(), self.payload())
        self.assertEqual(response.status_code, 302, getattr(response, 'content', b'')[:800])
        titulo = TituloFinanceiro.objects.get(matriz=self.matriz, entidade_nome='Motoboy F32')
        self.assertEqual(titulo.status, TituloFinanceiro.Status.LIQUIDADO)
        baixa = BaixaFinanceira.objects.get(parcela__titulo=titulo, tipo=BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.valor, Decimal('15.00'))
        self.assertEqual(baixa.sessao_caixa_id, self.sessao.pk)
        self.assertEqual(baixa.movimentacao_caixa.tipo, TipoMovimentacaoCaixa.SANGRIA)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao), Decimal('85.00'))

    def test_sem_sessao_reverte_criacao_titulo(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR)
        MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao).delete()
        self.sessao.delete()
        self.client.force_login(self.operador)
        response = self.client.post(self.url(), self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').exists())

    def test_retry_nao_duplica_titulo_baixa_ou_sangria(self):
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR)
        self.client.force_login(self.operador)
        data = self.payload()
        self.assertEqual(self.client.post(self.url(), data).status_code, 302)
        self.assertEqual(self.client.post(self.url(), data).status_code, 302)
        self.assertEqual(TituloFinanceiro.objects.filter(matriz=self.matriz, entidade_nome='Motoboy F32').count(), 1)
        self.assertEqual(BaixaFinanceira.objects.filter(parcela__titulo__matriz=self.matriz, tipo=BaixaFinanceira.Tipo.BAIXA).count(), 1)
        self.assertEqual(MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao, tipo=TipoMovimentacaoCaixa.SANGRIA).count(), 1)