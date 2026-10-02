from datetime import date
from decimal import Decimal

from django.test import TestCase

from empresas.models import Loja, Matriz, StatusOperacional
from financeiro.models import TituloFinanceiro
from financeiro.services import (
    criar_titulo_financeiro,
    estornar_baixa_financeira,
    registrar_baixa_financeira,
)


class FluxoCaixaSelectorContractTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F2C")
        self.loja_a = Loja.objects.create(
            matriz=self.matriz, nome="Loja F2C A", status=StatusOperacional.ATIVA
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz, nome="Loja F2C B", status=StatusOperacional.ATIVA
        )

    def titulo(self, natureza, chave, valor, vencimento, loja=None):
        return criar_titulo_financeiro(
            matriz=self.matriz,
            loja=loja,
            natureza=natureza,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave,
            chave_idempotencia=chave,
            descricao=chave,
            data_emissao=date(2026, 9, 1),
            parcelas=[{"numero": 1, "vencimento": vencimento, "valor": Decimal(valor)}],
        )

    def fluxo(self, **kwargs):
        from financeiro.selectors import resumo_fluxo_caixa
        return resumo_fluxo_caixa(matriz=self.matriz, **kwargs)

    def test_realizado_usa_data_evento_e_estorno_reverte_no_periodo(self):
        receber = self.titulo(
            TituloFinanceiro.Natureza.RECEBER, "F2C-R1", "100.00",
            date(2026, 10, 20), self.loja_a
        )
        pagar = self.titulo(
            TituloFinanceiro.Natureza.PAGAR, "F2C-P1", "80.00",
            date(2026, 10, 20), self.loja_a
        )
        baixa_r = registrar_baixa_financeira(
            parcela=receber.parcelas.get(), valor=Decimal("60.00"),
            data=date(2026, 10, 5), chave_idempotencia="F2C-BR1"
        )
        registrar_baixa_financeira(
            parcela=pagar.parcelas.get(), valor=Decimal("30.00"),
            data=date(2026, 10, 6), chave_idempotencia="F2C-BP1"
        )
        estornar_baixa_financeira(
            baixa=baixa_r, valor=Decimal("10.00"),
            data=date(2026, 10, 7), chave_idempotencia="F2C-ER1"
        )

        resumo = self.fluxo(data_inicio=date(2026, 10, 5), data_fim=date(2026, 10, 7))

        self.assertEqual(resumo["realizado_entradas"], Decimal("50.00"))
        self.assertEqual(resumo["realizado_saidas"], Decimal("30.00"))
        self.assertEqual(resumo["realizado_liquido"], Decimal("20.00"))

    def test_realizado_respeita_limites_inclusivos_do_periodo(self):
        receber = self.titulo(
            TituloFinanceiro.Natureza.RECEBER, "F2C-R2", "100.00",
            date(2026, 11, 20), self.loja_a
        )
        parcela = receber.parcelas.get()
        registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("10.00"),
            data=date(2026, 10, 4), chave_idempotencia="F2C-BR2A"
        )
        registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("20.00"),
            data=date(2026, 10, 5), chave_idempotencia="F2C-BR2B"
        )
        registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("30.00"),
            data=date(2026, 10, 7), chave_idempotencia="F2C-BR2C"
        )
        registrar_baixa_financeira(
            parcela=parcela, valor=Decimal("40.00"),
            data=date(2026, 10, 8), chave_idempotencia="F2C-BR2D"
        )

        resumo = self.fluxo(data_inicio=date(2026, 10, 5), data_fim=date(2026, 10, 7))
        self.assertEqual(resumo["realizado_entradas"], Decimal("50.00"))

    def test_previsto_usa_vencimento_e_saldo_aberto(self):
        receber = self.titulo(
            TituloFinanceiro.Natureza.RECEBER, "F2C-R3", "100.00",
            date(2026, 10, 10), self.loja_a
        )
        self.titulo(
            TituloFinanceiro.Natureza.PAGAR, "F2C-P3", "70.00",
            date(2026, 10, 15), self.loja_a
        )
        self.titulo(
            TituloFinanceiro.Natureza.RECEBER, "F2C-FORA", "999.00",
            date(2026, 11, 1), self.loja_a
        )
        registrar_baixa_financeira(
            parcela=receber.parcelas.get(), valor=Decimal("25.00"),
            data=date(2026, 10, 2), chave_idempotencia="F2C-BR3"
        )

        resumo = self.fluxo(data_inicio=date(2026, 10, 1), data_fim=date(2026, 10, 31))
        self.assertEqual(resumo["previsto_receber"], Decimal("75.00"))
        self.assertEqual(resumo["previsto_pagar"], Decimal("70.00"))
        self.assertEqual(resumo["previsto_liquido"], Decimal("5.00"))

    def test_escopo_loja_isola_realizado_e_previsto(self):
        a = self.titulo(
            TituloFinanceiro.Natureza.RECEBER, "F2C-LA", "100.00",
            date(2026, 10, 10), self.loja_a
        )
        b = self.titulo(
            TituloFinanceiro.Natureza.RECEBER, "F2C-LB", "200.00",
            date(2026, 10, 10), self.loja_b
        )
        registrar_baixa_financeira(
            parcela=a.parcelas.get(), valor=Decimal("40.00"),
            data=date(2026, 10, 5), chave_idempotencia="F2C-LA-B"
        )
        registrar_baixa_financeira(
            parcela=b.parcelas.get(), valor=Decimal("80.00"),
            data=date(2026, 10, 5), chave_idempotencia="F2C-LB-B"
        )

        resumo = self.fluxo(
            data_inicio=date(2026, 10, 1), data_fim=date(2026, 10, 31),
            loja=self.loja_a
        )
        self.assertEqual(resumo["realizado_entradas"], Decimal("40.00"))
        self.assertEqual(resumo["previsto_receber"], Decimal("60.00"))

    def test_loja_de_outra_matriz_nao_vaza_dados(self):
        outra = Matriz.objects.create(nome="Outra Matriz F2C")
        loja_outra = Loja.objects.create(
            matriz=outra, nome="Loja Outra F2C", status=StatusOperacional.ATIVA
        )
        resumo = self.fluxo(
            data_inicio=date(2026, 10, 1), data_fim=date(2026, 10, 31),
            loja=loja_outra
        )
        self.assertEqual(resumo["realizado_entradas"], Decimal("0.00"))
        self.assertEqual(resumo["realizado_saidas"], Decimal("0.00"))
        self.assertEqual(resumo["previsto_receber"], Decimal("0.00"))
        self.assertEqual(resumo["previsto_pagar"], Decimal("0.00"))