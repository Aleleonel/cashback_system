from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from empresas.models import Matriz, Loja
from financeiro.models import TituloFinanceiro
from financeiro.services import (
    criar_titulo_financeiro,
    registrar_baixa_financeira,
    estornar_baixa_financeira,
)
from pdv.choices import StatusOperacaoVenda, StatusSessaoCaixa, TipoFormaPagamento
from pdv.choices import TipoMovimentacaoCaixa
from pdv.models import Caixa, FormaPagamento, MovimentacaoCaixa, PagamentoVenda, SessaoCaixa, Venda


class F2EA21DemonstrativoCaixaDBTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.matriz = Matriz.objects.create(nome="Matriz F2EA21Q")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F2EA21Q")
        self.admin = U.objects.create_user(
            username="admin_f2ea21q", password="x", perfil="admin_loja", matriz=self.matriz
        )
        self.caixa = Caixa.objects.create(
            matriz=self.matriz, loja=self.loja, nome="Caixa F2EA21Q", codigo="F2EA21Q"
        )
        self.sessao = SessaoCaixa.objects.create(
            caixa=self.caixa, operador_abertura=self.admin, valor_abertura=Decimal("100.00")
        )
        MovimentacaoCaixa.objects.create(
            sessao_caixa=self.sessao,
            tipo=TipoMovimentacaoCaixa.ABERTURA,
            valor=Decimal("100.00"),
            operador=self.admin,
            descricao="Abertura F2EA21Q",
        )
        self.dinheiro = FormaPagamento.objects.create(
            matriz=self.matriz, nome="Dinheiro F2EA21Q", codigo="DIN_F2EA21Q",
            tipo=TipoFormaPagamento.DINHEIRO, gera_contas_receber=False,
            movimenta_caixa=True, ativa=True,
        )
        self.crediario = FormaPagamento.objects.create(
            matriz=self.matriz, nome="Crediario F2EA21Q", codigo="CRD_F2EA21Q",
            tipo=TipoFormaPagamento.OUTRO, gera_contas_receber=True,
            movimenta_caixa=False, ativa=True,
        )
        self.client.force_login(self.admin)

    def venda(self, *, status, forma, valor):
        v = Venda.objects.create(
            matriz=self.matriz, loja=self.loja, sessao_caixa=self.sessao,
            operador=self.admin, vendedor=self.admin, status=status,
            subtotal=valor, total=valor,
            finalizada_em=timezone.now() if status == StatusOperacaoVenda.FINALIZADA else None,
        )
        p = PagamentoVenda.objects.create(
            venda=v, forma_pagamento=forma, valor=valor, parcelas=1
        )
        return v, p

    def titulo_receber(self, pagamento, valor):
        return criar_titulo_financeiro(
            matriz=self.matriz,
            loja=self.loja,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO,
            origem_id=str(pagamento.uuid),
            chave_idempotencia=f"f2ea21q:{pagamento.uuid}",
            descricao="F2EA21Q contas a receber",
            data_emissao=date.today(),
            parcelas=[{"numero": 1, "vencimento": date.today(), "valor": valor}],
        )

    def get_demo(self):
        return self.client.get(
            reverse("pdv:demonstrativo_caixa", kwargs={"sessao_id": self.sessao.pk})
        )

    def linha(self, response, nome):
        return next(x for x in response.context["formas_pagamento"] if x["nome"] == nome)

    def test_pagamento_imediato_finalizado_entra_como_recebido(self):
        self.venda(status=StatusOperacaoVenda.FINALIZADA, forma=self.dinheiro, valor=Decimal("30.00"))
        r = self.get_demo()
        self.assertEqual(r.status_code, 200)
        linha = self.linha(r, self.dinheiro.nome)
        self.assertEqual(linha["recebido"], Decimal("30.00"))
        self.assertEqual(linha["a_receber"], Decimal("0.00"))
        self.assertEqual(linha["total"], Decimal("30.00"))

    def test_venda_nao_finalizada_nao_contamina_demonstrativo(self):
        self.venda(status=StatusOperacaoVenda.CANCELADA, forma=self.dinheiro, valor=Decimal("99.00"))
        r = self.get_demo()
        self.assertEqual(r.status_code, 200)
        self.assertFalse(any(x["nome"] == self.dinheiro.nome for x in r.context["formas_pagamento"]))

    def test_crediario_sem_baixa_fica_integralmente_a_receber(self):
        _, p = self.venda(status=StatusOperacaoVenda.FINALIZADA, forma=self.crediario, valor=Decimal("100.00"))
        self.titulo_receber(p, Decimal("100.00"))
        r = self.get_demo()
        linha = self.linha(r, self.crediario.nome)
        self.assertEqual(linha["recebido"], Decimal("0.00"))
        self.assertEqual(linha["a_receber"], Decimal("100.00"))

    def test_crediario_baixa_parcial_e_estorno_usam_ledger_financeiro(self):
        _, p = self.venda(status=StatusOperacaoVenda.FINALIZADA, forma=self.crediario, valor=Decimal("100.00"))
        titulo = self.titulo_receber(p, Decimal("100.00"))
        parcela = titulo.parcelas.get()
        baixa = registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("60.00"), data=date.today(),
            chave_idempotencia="f2ea21q-baixa",
        )
        r = self.get_demo()
        linha = self.linha(r, self.crediario.nome)
        self.assertEqual(linha["recebido"], Decimal("60.00"))
        self.assertEqual(linha["a_receber"], Decimal("40.00"))

        estornar_baixa_financeira(
            baixa=baixa, valor=Decimal("20.00"), data=date.today(),
            chave_idempotencia="f2ea21q-estorno",
        )
        r = self.get_demo()
        linha = self.linha(r, self.crediario.nome)
        self.assertEqual(linha["recebido"], Decimal("40.00"))
        self.assertEqual(linha["a_receber"], Decimal("60.00"))

    def test_sessao_aberta_nao_inventa_saldo_real(self):
        r = self.get_demo()
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.context["saldo_real"])
        self.assertEqual(r.context["saldo_calculado"], Decimal("100.00"))

    def test_sessao_fechada_expoe_informado_calculado_e_diferenca(self):
        self.sessao.status = StatusSessaoCaixa.FECHADA
        self.sessao.valor_fechamento_informado = Decimal("98.00")
        self.sessao.valor_fechamento_calculado = Decimal("100.00")
        self.sessao.diferenca_fechamento = Decimal("-2.00")
        self.sessao.fechada_em = timezone.now()
        self.sessao.operador_fechamento = self.admin
        self.sessao.save()
        r = self.get_demo()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["saldo_real"], Decimal("98.00"))
        self.assertEqual(r.context["sessao"].valor_fechamento_calculado, Decimal("100.00"))
        self.assertEqual(r.context["sessao"].diferenca_fechamento, Decimal("-2.00"))