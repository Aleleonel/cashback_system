from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR
from empresas.models import Loja, Matriz
from financeiro.forms import LancamentoManualForm
from financeiro.models import TituloFinanceiro, ContaFinanceira
from financeiro.tests_f32p4h88q4e39f_pagamento_imediato import PagamentoImediatoF32Tests
from pdv.models import FormaPagamento, MovimentacaoCaixa
from pdv.choices import TipoMovimentacaoCaixa


from django.test import TestCase


class PagamentoImediatoEscopoLojaF32Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        PagamentoImediatoF32Tests.setUpTestData.__func__(cls)

    payload = PagamentoImediatoF32Tests.payload
    url = PagamentoImediatoF32Tests.url

    def setUp(self):
        PermissaoUsuario.objects.get_or_create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR)
        self.outra_loja = Loja.objects.create(matriz=self.matriz, nome='F32 Outra Loja')
        self.client.force_login(self.operador)

    def test_operador_nao_pode_escolher_outra_loja_no_post(self):
        before = TituloFinanceiro.objects.count()
        response = self.client.post(self.url(), self.payload(loja=str(self.outra_loja.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TituloFinanceiro.objects.count(), before)
        self.assertFalse(MovimentacaoCaixa.objects.filter(tipo=TipoMovimentacaoCaixa.SANGRIA).exists())

    def test_operador_nao_pode_escolher_forma_pagamento_de_outra_matriz(self):
        matriz_externa = Matriz.objects.create(nome='F32 Matriz Externa')
        forma_externa = FormaPagamento.objects.create(
            matriz=matriz_externa, nome='F32 Dinheiro Externo', codigo='DIN_F32_EXT',
            tipo=self.dinheiro.tipo, movimenta_caixa=True, ativa=True,
        )
        before = TituloFinanceiro.objects.count()
        response = self.client.post(self.url(), self.payload(forma_pagamento_imediato=str(forma_externa.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TituloFinanceiro.objects.count(), before)
        self.assertFalse(MovimentacaoCaixa.objects.filter(tipo=TipoMovimentacaoCaixa.SANGRIA).exists())

    def test_formulario_nao_oferece_conta_de_outra_loja(self):
        # O filtro deve excluir contas explicitamente vinculadas a outra loja.
        # Inspecao do queryset, sem depender de atributos obrigatorios do cadastro de contas.
        form = LancamentoManualForm(matriz=self.matriz, lojas=Loja.objects.filter(pk=self.loja.pk))
        self.assertFalse(form.fields['conta_financeira_imediata'].queryset.filter(loja=self.outra_loja).exists())

    def test_loja_operacional_fica_restrita_no_get(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['form'].fields['loja'].queryset.values_list('pk', flat=True)), [self.loja.pk])