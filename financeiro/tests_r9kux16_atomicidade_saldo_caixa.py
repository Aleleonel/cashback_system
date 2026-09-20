from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Loja, Matriz
from financeiro.models import BaixaFinanceira, TituloFinanceiro
from financeiro.services import criar_titulo_financeiro, registrar_baixa_financeira_com_caixa
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.models import Caixa, FormaPagamento, MovimentacaoCaixa, SessaoCaixa


class R9KUX16AtomicidadeFinanceiroCaixaRedTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz R9KUX16B4")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja R9KUX16B4")
        User = get_user_model()
        self.user = User.objects.create_user(
            username="r9kux16b4", password="x", matriz=self.matriz
        )
        self.user.lojas.add(self.loja)
        self.caixa = Caixa.objects.create(
            matriz=self.matriz, loja=self.loja, nome="Caixa R9KUX16B4", codigo="CX16B4"
        )
        self.sessao = SessaoCaixa.objects.create(
            caixa=self.caixa, operador_abertura=self.user, valor_abertura=Decimal("0.00")
        )
        self.dinheiro = FormaPagamento.objects.create(
            matriz=self.matriz, nome="Dinheiro R9KUX16B4", codigo="DIN16B4",
            tipo=TipoFormaPagamento.DINHEIRO, movimenta_caixa=True, ativa=True
        )
        self.titulo = criar_titulo_financeiro(
            matriz=self.matriz, loja=self.loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id="r9kux16b4", chave_idempotencia="r9kux16b4",
            descricao="Despesa sem saldo", data_emissao=date.today(),
            parcelas=[{"numero": 1, "vencimento": date.today(), "valor": Decimal("15.00")}],
        )
        self.parcela = self.titulo.parcelas.get()

    def test_baixa_dinheiro_sem_saldo_rejeita_e_reverte_todos_os_efeitos(self):
        with self.assertRaises(ValidationError):
            registrar_baixa_financeira_com_caixa(
                parcela=self.parcela, valor=Decimal("15.00"), data=date.today(),
                chave_idempotencia="r9kux16b4-baixa", forma_pagamento=self.dinheiro,
                sessao_caixa=self.sessao, operador=self.user,
            )

        self.parcela.refresh_from_db()
        self.titulo.refresh_from_db()

        self.assertFalse(
            BaixaFinanceira.objects.filter(parcela=self.parcela).exists()
        )
        self.assertFalse(
            MovimentacaoCaixa.objects.filter(
                sessao_caixa=self.sessao,
                tipo=TipoMovimentacaoCaixa.SANGRIA,
            ).exists()
        )
        self.assertEqual(self.parcela.status, self.parcela.Status.ABERTO)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.ABERTO)