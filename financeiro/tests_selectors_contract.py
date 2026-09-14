from datetime import date
from decimal import Decimal

from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro, registrar_baixa_financeira
from financeiro.selectors import listar_titulos, parcelas_em_aberto, resumo_saldos


class SelectorsFinanceirosContractTest(TestCase):
    def setUp(self):
        self.matriz_a = Matriz.objects.create(nome="Matriz Selectors A")
        self.matriz_b = Matriz.objects.create(nome="Matriz Selectors B")
        self.receber = criar_titulo_financeiro(
            matriz=self.matriz_a, loja=None, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL, origem_id="SEL-R",
            chave_idempotencia="SEL-R", descricao="Receber A", data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,10),"valor":Decimal("100.00")}],
        )
        self.pagar = criar_titulo_financeiro(
            matriz=self.matriz_a, loja=None, natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL, origem_id="SEL-P",
            chave_idempotencia="SEL-P", descricao="Pagar A", data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,20),"valor":Decimal("80.00")}],
        )
        criar_titulo_financeiro(
            matriz=self.matriz_b, loja=None, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL, origem_id="SEL-B",
            chave_idempotencia="SEL-B", descricao="Receber B", data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,15),"valor":Decimal("999.00")}],
        )

    def test_listar_titulos_isola_matriz(self):
        self.assertEqual(listar_titulos(matriz=self.matriz_a).count(), 2)

    def test_listar_titulos_filtra_natureza(self):
        qs=listar_titulos(matriz=self.matriz_a, natureza=TituloFinanceiro.Natureza.RECEBER)
        self.assertEqual(list(qs.values_list("pk", flat=True)), [self.receber.pk])

    def test_parcelas_em_aberto_ordena_por_vencimento(self):
        parcelas=list(parcelas_em_aberto(matriz=self.matriz_a))
        self.assertEqual([p.titulo_id for p in parcelas], [self.receber.pk, self.pagar.pk])

    def test_parcelas_em_aberto_exclui_liquidada(self):
        parcela=self.receber.parcelas.get()
        registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("100.00"), data=date(2026,9,14),
            chave_idempotencia="SEL-BX",
        )
        ids=list(parcelas_em_aberto(matriz=self.matriz_a).values_list("titulo_id", flat=True))
        self.assertNotIn(self.receber.pk, ids)
        self.assertIn(self.pagar.pk, ids)

    def test_resumo_saldos_deriva_baixas(self):
        parcela=self.receber.parcelas.get()
        registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("30.00"), data=date(2026,9,14),
            chave_idempotencia="SEL-BX-30",
        )
        resumo=resumo_saldos(matriz=self.matriz_a)
        self.assertEqual(resumo["receber"], Decimal("70.00"))
        self.assertEqual(resumo["pagar"], Decimal("80.00"))

    def test_resumo_saldos_isola_matriz(self):
        resumo=resumo_saldos(matriz=self.matriz_a)
        self.assertEqual(resumo["receber"], Decimal("100.00"))
        self.assertEqual(resumo["pagar"], Decimal("80.00"))