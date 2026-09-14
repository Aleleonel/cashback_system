from datetime import date
from decimal import Decimal

from django.test import TestCase

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import (
    cancelar_titulo_financeiro,
    criar_titulo_financeiro,
    estornar_baixa_financeira,
    registrar_baixa_financeira,
)
from financeiro.selectors import listar_titulos, parcelas_em_aberto, resumo_saldos


class SelectorsHardeningContractTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Hardening")
        self.loja_a = Loja.objects.create(matriz=self.matriz, nome="Loja A", status=StatusOperacional.ATIVA)
        self.loja_b = Loja.objects.create(matriz=self.matriz, nome="Loja B", status=StatusOperacional.ATIVA)
        self.titulo_a = criar_titulo_financeiro(
            matriz=self.matriz, loja=self.loja_a, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL, origem_id="HARD-A",
            chave_idempotencia="HARD-A", descricao="Titulo A", data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,10),"valor":Decimal("100.00")}],
        )
        self.titulo_b = criar_titulo_financeiro(
            matriz=self.matriz, loja=self.loja_b, natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL, origem_id="HARD-B",
            chave_idempotencia="HARD-B", descricao="Titulo B", data_emissao=date(2026,9,14),
            parcelas=[{"numero":1,"vencimento":date(2026,10,20),"valor":Decimal("50.00")}],
        )

    def test_segmentacao_loja_listar_titulos(self):
        ids=list(listar_titulos(matriz=self.matriz, loja=self.loja_a).values_list("pk", flat=True))
        self.assertEqual(ids, [self.titulo_a.pk])

    def test_segmentacao_loja_parcelas_abertas(self):
        ids=list(parcelas_em_aberto(matriz=self.matriz, loja=self.loja_b).values_list("titulo_id", flat=True))
        self.assertEqual(ids, [self.titulo_b.pk])

    def test_segmentacao_loja_resumo(self):
        resumo=resumo_saldos(matriz=self.matriz, loja=self.loja_a)
        self.assertEqual(resumo["receber"], Decimal("100.00"))

    def test_cancelado_nao_entra_parcelas_abertas_nem_resumo(self):
        cancelar_titulo_financeiro(titulo=self.titulo_a)
        ids=list(parcelas_em_aberto(matriz=self.matriz).values_list("titulo_id", flat=True))
        self.assertNotIn(self.titulo_a.pk, ids)
        self.assertEqual(resumo_saldos(matriz=self.matriz)["receber"], Decimal("50.00"))

    def test_estorno_reabre_e_recompoe_saldo(self):
        parcela=self.titulo_a.parcelas.get()
        baixa=registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("100.00"), data=date(2026,9,14),
            chave_idempotencia="HARD-BX",
        )
        self.assertNotIn(self.titulo_a.pk, list(parcelas_em_aberto(matriz=self.matriz).values_list("titulo_id", flat=True)))
        estornar_baixa_financeira(
            baixa=baixa, valor=Decimal("40.00"), data=date(2026,9,15),
            chave_idempotencia="HARD-EST",
        )
        self.assertIn(self.titulo_a.pk, list(parcelas_em_aberto(matriz=self.matriz).values_list("titulo_id", flat=True)))
        self.assertEqual(resumo_saldos(matriz=self.matriz)["receber"], Decimal("90.00"))

    def test_loja_de_outra_matriz_nao_vaza_dados(self):
        outra=Matriz.objects.create(nome="Outra Matriz")
        loja_outra=Loja.objects.create(matriz=outra, nome="Loja Outra", status=StatusOperacional.ATIVA)
        self.assertEqual(listar_titulos(matriz=self.matriz, loja=loja_outra).count(), 0)
        self.assertEqual(parcelas_em_aberto(matriz=self.matriz, loja=loja_outra).count(), 0)
        self.assertEqual(resumo_saldos(matriz=self.matriz, loja=loja_outra)["receber"], Decimal("0.00"))