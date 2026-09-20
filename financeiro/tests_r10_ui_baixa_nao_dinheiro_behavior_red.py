import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR
from empresas.models import Loja, Matriz
from financeiro.models import BaixaFinanceira, ContaFinanceira, TituloFinanceiro
from financeiro.services import criar_titulo_financeiro
from pdv.choices import TipoFormaPagamento
from pdv.models import FormaPagamento, MovimentacaoCaixa


class R10UIBaixaNaoDinheiroBehaviorREDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz R10F", cnpj="95959595000195")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja R10F")
        cls.operador = Usuario.objects.create_user(
            username="r10f_operador", password="SenhaTeste123!",
            matriz=cls.matriz, perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.operador.lojas.add(cls.loja)
        PermissaoUsuario.objects.create(
            usuario=cls.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR,
        )
        cls.pix = FormaPagamento.objects.create(
            matriz=cls.matriz, nome="PIX R10F", codigo="PIX_R10F",
            tipo=TipoFormaPagamento.PIX, movimenta_caixa=False, ativa=True,
        )
        cls.conta = ContaFinanceira.objects.create(
            matriz=cls.matriz, loja=cls.loja, tipo="BANCO",
            nome="Conta PIX R10F", agencia="", numero="", digito="", chave_pix="pix-r10f",
            ativo=True,
        )
        cls.titulo = criar_titulo_financeiro(
            matriz=cls.matriz, loja=cls.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id="r10f", chave_idempotencia="r10f",
            descricao="Despesa PIX R10F", data_emissao=date.today(),
            parcelas=[{"numero": 1, "vencimento": date.today(), "valor": Decimal("15.00")}],
        )
        cls.parcela = cls.titulo.parcelas.get()

    def url(self):
        return reverse(
            "financeiro:parcela_baixa_nova",
            kwargs={"titulo_uuid": self.titulo.uuid, "parcela_id": self.parcela.pk},
        )

    def test_get_exibe_pix_e_conta_financeira_autorizada(self):
        self.client.force_login(self.operador)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pix.nome)
        self.assertContains(response, self.conta.nome)

    def test_post_pix_sem_sessao_caixa_cria_baixa_sem_movimento_fisico(self):
        self.client.force_login(self.operador)
        response = self.client.post(self.url(), {
            "valor": "15.00",
            "data": date.today().isoformat(),
            "observacao": "Pagamento PIX R10F",
            "forma_pagamento": str(self.pix.pk),
            "conta_financeira": str(self.conta.pk),
            "chave_idempotencia": str(uuid.uuid4()),
        })
        self.assertEqual(response.status_code, 302)
        baixa = self.parcela.baixas.get(tipo=BaixaFinanceira.Tipo.BAIXA)
        self.assertEqual(baixa.forma_pagamento_id, self.pix.pk)
        self.assertEqual(baixa.conta_financeira_id, self.conta.pk)
        self.assertIsNone(baixa.sessao_caixa_id)
        self.assertIsNone(baixa.movimentacao_caixa_id)
        self.assertEqual(MovimentacaoCaixa.objects.count(), 0)

    def test_conta_de_outra_loja_nao_aparece_e_post_nao_cria_baixa(self):
        outra_loja = Loja.objects.create(matriz=self.matriz, nome="Outra Loja R10F")
        outra_conta = ContaFinanceira.objects.create(
            matriz=self.matriz, loja=outra_loja, tipo="BANCO",
            nome="Conta Outra Loja R10F", agencia="", numero="", digito="", chave_pix="outra-r10f",
            ativo=True,
        )
        self.client.force_login(self.operador)
        get_response = self.client.get(self.url())
        self.assertNotContains(get_response, outra_conta.nome)
        post_response = self.client.post(self.url(), {
            "valor": "15.00", "data": date.today().isoformat(),
            "forma_pagamento": str(self.pix.pk),
            "conta_financeira": str(outra_conta.pk),
            "chave_idempotencia": str(uuid.uuid4()),
        })
        self.assertEqual(post_response.status_code, 200)
        self.assertFalse(self.parcela.baixas.exists())

    def test_conta_global_da_matriz_e_permitida(self):
        global_conta = ContaFinanceira.objects.create(
            matriz=self.matriz, loja=None, tipo="BANCO",
            nome="Conta Global R10F", agencia="", numero="", digito="", chave_pix="global-r10f",
            ativo=True,
        )
        self.client.force_login(self.operador)
        response = self.client.get(self.url())
        self.assertContains(response, global_conta.nome)