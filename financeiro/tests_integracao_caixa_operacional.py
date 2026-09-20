from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from empresas.models import Matriz, Loja
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro, registrar_baixa_financeira_com_caixa, estornar_baixa_financeira_com_caixa
from pdv.choices import TipoFormaPagamento, TipoMovimentacaoCaixa
from pdv.models import Caixa, SessaoCaixa, FormaPagamento, MovimentacaoCaixa
from pdv.services.vendas.caixa import calcular_saldo_sessao_caixa

class IntegracaoCaixaOperacionalTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.user=U.objects.create_user(username="r7df", password="x")
        self.matriz=Matriz.objects.create(nome="Matriz R7DF")
        self.loja=Loja.objects.create(matriz=self.matriz, nome="Loja R7DF")
        self.caixa=Caixa.objects.create(matriz=self.matriz, loja=self.loja, nome="Caixa R7DF", codigo="R7DF")
        self.sessao=SessaoCaixa.objects.create(caixa=self.caixa, operador_abertura=self.user, valor_abertura=Decimal("100.00"))
        MovimentacaoCaixa.objects.create(sessao_caixa=self.sessao,tipo=TipoMovimentacaoCaixa.ABERTURA,valor=Decimal("100.00"),operador=self.user,descricao="Abertura")
        self.dinheiro=FormaPagamento.objects.create(matriz=self.matriz,nome="Dinheiro R7DF",codigo="DIN_R7DF",tipo=TipoFormaPagamento.DINHEIRO,movimenta_caixa=True)
        self.pix=FormaPagamento.objects.create(matriz=self.matriz,nome="PIX R7DF",codigo="PIX_R7DF",tipo=TipoFormaPagamento.PIX,movimenta_caixa=False)

    def titulo(self,natureza,chave,valor="30.00"):
        return criar_titulo_financeiro(
            matriz=self.matriz,loja=self.loja,natureza=natureza,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,origem_id=chave,
            chave_idempotencia=chave,descricao=chave,data_emissao=date.today(),
            parcelas=[{"numero":1,"vencimento":date.today()+timedelta(days=1),"valor":Decimal(valor)}],
        )

    def test_pagar_dinheiro_gera_sangria_e_estorno_recompoe_saldo(self):
        t=self.titulo(TituloFinanceiro.Natureza.PAGAR,"r7df-pagar")
        p=t.parcelas.get()
        b=registrar_baixa_financeira_com_caixa(parcela=p,valor=Decimal("30"),data=date.today(),chave_idempotencia="bx-pagar",forma_pagamento=self.dinheiro,sessao_caixa=self.sessao,operador=self.user)
        self.assertEqual(b.movimentacao_caixa.tipo,TipoMovimentacaoCaixa.SANGRIA)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao),Decimal("70.00"))
        e=estornar_baixa_financeira_com_caixa(baixa=b,valor=Decimal("30"),data=date.today(),chave_idempotencia="est-pagar",operador=self.user)
        self.assertEqual(e.movimentacao_caixa.tipo,TipoMovimentacaoCaixa.ESTORNO)
        self.assertEqual(e.movimentacao_caixa.movimentacao_estornada_id,b.movimentacao_caixa_id)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao),Decimal("100.00"))

    def test_receber_dinheiro_gera_suprimento_e_estorno_recompoe_saldo(self):
        t=self.titulo(TituloFinanceiro.Natureza.RECEBER,"r7df-receber")
        p=t.parcelas.get()
        b=registrar_baixa_financeira_com_caixa(parcela=p,valor=Decimal("30"),data=date.today(),chave_idempotencia="bx-receber",forma_pagamento=self.dinheiro,sessao_caixa=self.sessao,operador=self.user)
        self.assertEqual(b.movimentacao_caixa.tipo,TipoMovimentacaoCaixa.SUPRIMENTO)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao),Decimal("130.00"))
        estornar_baixa_financeira_com_caixa(baixa=b,valor=Decimal("30"),data=date.today(),chave_idempotencia="est-receber",operador=self.user)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao),Decimal("100.00"))

    def test_reprocessamento_baixa_dinheiro_nao_duplica_movimento(self):
        t=self.titulo(TituloFinanceiro.Natureza.PAGAR,"r7df-idem")
        p=t.parcelas.get()
        kw=dict(parcela=p,valor=Decimal("30"),data=date.today(),chave_idempotencia="bx-idem",forma_pagamento=self.dinheiro,sessao_caixa=self.sessao,operador=self.user)
        a=registrar_baixa_financeira_com_caixa(**kw); b=registrar_baixa_financeira_com_caixa(**kw)
        self.assertEqual(a.pk,b.pk);self.assertEqual(a.movimentacao_caixa_id,b.movimentacao_caixa_id)
        self.assertEqual(MovimentacaoCaixa.objects.filter(sessao_caixa=self.sessao,tipo=TipoMovimentacaoCaixa.SANGRIA).count(),1)

    def test_pix_nao_gera_movimento_caixa_fisico(self):
        t=self.titulo(TituloFinanceiro.Natureza.PAGAR,"r7df-pix")
        b=registrar_baixa_financeira_com_caixa(parcela=t.parcelas.get(),valor=Decimal("30"),data=date.today(),chave_idempotencia="bx-pix",forma_pagamento=self.pix)
        self.assertIsNone(b.movimentacao_caixa_id);self.assertIsNone(b.sessao_caixa_id)
        self.assertEqual(calcular_saldo_sessao_caixa(sessao=self.sessao),Decimal("100.00"))

    def test_dinheiro_rejeita_sessao_de_outra_loja(self):
        outra=Loja.objects.create(matriz=self.matriz,nome="Outra R7DF")
        cx=Caixa.objects.create(matriz=self.matriz,loja=outra,nome="Outro Caixa",codigo="OUT_R7DF")
        # mesmo operador nao pode ter duas sessoes abertas; usa outro operador
        u2=get_user_model().objects.create_user(username="r7df2",password="x")
        s2=SessaoCaixa.objects.create(caixa=cx,operador_abertura=u2,valor_abertura=Decimal("0"))
        t=self.titulo(TituloFinanceiro.Natureza.PAGAR,"r7df-loja")
        with self.assertRaises(ValidationError):
            registrar_baixa_financeira_com_caixa(parcela=t.parcelas.get(),valor=Decimal("30"),data=date.today(),chave_idempotencia="bx-loja",forma_pagamento=self.dinheiro,sessao_caixa=s2,operador=u2)