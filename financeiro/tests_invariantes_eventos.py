from datetime import date
from decimal import Decimal
from django.test import TestCase
from empresas.models import Matriz
from financeiro.models import BaixaFinanceira, ParcelaFinanceira, TituloFinanceiro
from financeiro.services import criar_titulo_financeiro, registrar_baixa_financeira, estornar_baixa_financeira

class InvariantesSequenciaEventosFinanceirosTests(TestCase):
    def setUp(self):
        self.matriz=Matriz.objects.create(nome="Matriz Sequencia")
        self.titulo=criar_titulo_financeiro(
            matriz=self.matriz, loja=None, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo="MANUAL", origem_id="seq-001", chave_idempotencia="titulo-seq-001",
            descricao="Sequencia eventos", data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,14),"valor":Decimal("100.00")}],
        )
        self.parcela=self.titulo.parcelas.get(numero=1)

    def test_baixa_estorno_nova_baixa_preserva_ledger_e_status(self):
        b1=registrar_baixa_financeira(parcela=self.parcela,valor=Decimal("60.00"),data=date(2026,9,14),chave_idempotencia="seq-b1")
        estornar_baixa_financeira(baixa=b1,valor=Decimal("20.00"),data=date(2026,9,15),chave_idempotencia="seq-e1")
        registrar_baixa_financeira(parcela=self.parcela,valor=Decimal("60.00"),data=date(2026,9,16),chave_idempotencia="seq-b2")
        self.parcela.refresh_from_db(); self.titulo.refresh_from_db()
        self.assertEqual(BaixaFinanceira.objects.filter(parcela=self.parcela).count(),3)
        self.assertEqual(BaixaFinanceira.objects.filter(parcela=self.parcela,tipo=BaixaFinanceira.Tipo.BAIXA).count(),2)
        self.assertEqual(BaixaFinanceira.objects.filter(parcela=self.parcela,tipo=BaixaFinanceira.Tipo.ESTORNO).count(),1)
        liquido=sum((e.valor if e.tipo==BaixaFinanceira.Tipo.BAIXA else -e.valor) for e in self.parcela.baixas.all())
        self.assertEqual(liquido,Decimal("100.00"))
        self.assertEqual(self.parcela.status,ParcelaFinanceira.Status.LIQUIDADO)
        self.assertEqual(self.titulo.status,TituloFinanceiro.Status.LIQUIDADO)

    def test_liquidacao_estorno_total_reabertura_e_nova_liquidacao(self):
        b1=registrar_baixa_financeira(parcela=self.parcela,valor=Decimal("100.00"),data=date(2026,9,14),chave_idempotencia="seq2-b1")
        estornar_baixa_financeira(baixa=b1,valor=Decimal("100.00"),data=date(2026,9,15),chave_idempotencia="seq2-e1")
        self.parcela.refresh_from_db(); self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status,ParcelaFinanceira.Status.ABERTO)
        self.assertEqual(self.titulo.status,TituloFinanceiro.Status.ABERTO)
        registrar_baixa_financeira(parcela=self.parcela,valor=Decimal("100.00"),data=date(2026,9,16),chave_idempotencia="seq2-b2")
        self.parcela.refresh_from_db(); self.titulo.refresh_from_db()
        self.assertEqual(self.parcela.status,ParcelaFinanceira.Status.LIQUIDADO)
        self.assertEqual(self.titulo.status,TituloFinanceiro.Status.LIQUIDADO)
        self.assertEqual(self.parcela.baixas.count(),3)