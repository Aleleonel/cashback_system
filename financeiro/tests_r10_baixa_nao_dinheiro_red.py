from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz as Matriz
from financeiro.models import ContaFinanceira
from financeiro.services import (
    criar_titulo_financeiro,
    estornar_baixa_financeira_com_caixa,
    registrar_baixa_financeira_com_caixa,
)
from pdv.choices import TipoFormaPagamento
from pdv.models import FormaPagamento


class R10BaixaNaoDinheiroREDTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz R10 RED")
        self.user = get_user_model().objects.create_user(
            username="r10-red", password="x", matriz=self.matriz
        )
        self.pix = FormaPagamento.objects.create(
            matriz=self.matriz, nome="PIX R10", codigo="PIX_R10",
            tipo=TipoFormaPagamento.PIX, movimenta_caixa=False, ativa=True,
        )
        self.conta = ContaFinanceira.objects.create(
            matriz=self.matriz, nome="Conta PIX R10", tipo="corrente", ativo=True
        )
        self.titulo = criar_titulo_financeiro(
            matriz=self.matriz,
            loja=None,
            natureza="PAGAR",
            origem_tipo="MANUAL",
            origem_id="R10-001",
            chave_idempotencia="r10-red-titulo",
            descricao="Fornecedor R10",
            data_emissao=date.today(),
            parcelas=[{"numero": 1, "vencimento": date.today(), "valor": Decimal("100.00")}],
            usuario=self.user,
        )
        self.parcela = self.titulo.parcelas.get()

    def _baixar(self, **extra):
        dados = dict(
            parcela=self.parcela,
            valor=Decimal("100.00"),
            data=date.today(),
            chave_idempotencia="r10-red-pix",
            forma_pagamento=self.pix,
            conta_financeira=self.conta,
            usuario=self.user,
        )
        dados.update(extra)
        return registrar_baixa_financeira_com_caixa(**dados)

    def test_pix_persiste_conta_financeira_sem_caixa_fisico(self):
        baixa = self._baixar()
        self.assertEqual(baixa.forma_pagamento_id, self.pix.pk)
        self.assertEqual(baixa.conta_financeira_id, self.conta.pk)
        self.assertIsNone(baixa.sessao_caixa_id)
        self.assertIsNone(baixa.movimentacao_caixa_id)

    def test_conta_financeira_inativa_e_rejeitada(self):
        self.conta.ativo = False
        self.conta.save(update_fields=["ativo"])
        with self.assertRaises(ValidationError):
            self._baixar(chave_idempotencia="r10-red-inativa")
        self.assertEqual(self.parcela.baixas.count(), 0)

    def test_estorno_preserva_conta_financeira(self):
        baixa = self._baixar(chave_idempotencia="r10-red-estorno")
        estorno = estornar_baixa_financeira_com_caixa(
            baixa=baixa,
            valor=baixa.valor,
            data=date.today(),
            chave_idempotencia="r10-red-estorno-1",
            usuario=self.user,
        )
        self.assertEqual(estorno.forma_pagamento_id, self.pix.pk)
        self.assertEqual(estorno.conta_financeira_id, self.conta.pk)
        self.assertIsNone(estorno.movimentacao_caixa_id)