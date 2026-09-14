from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from empresas.models import Matriz
from financeiro.models import ParcelaFinanceira, TituloFinanceiro
from financeiro.services import (
    cancelar_titulo_financeiro,
    criar_titulo_financeiro,
    estornar_baixa_financeira,
    registrar_baixa_financeira,
)


class CancelamentoFinanceiroContractTest(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz Cancelamento")
        self.titulo = criar_titulo_financeiro(
            matriz=self.matriz,
            loja=None,
            natureza=TituloFinanceiro.Natureza.RECEBER,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id="CANCEL-1",
            chave_idempotencia="CANCEL-1",
            descricao="Titulo cancelamento",
            data_emissao=date(2026, 9, 14),
            parcelas=[
                {"numero": 1, "vencimento": date(2026, 10, 14), "valor": Decimal("60.00")},
                {"numero": 2, "vencimento": date(2026, 11, 14), "valor": Decimal("40.00")},
            ],
        )

    def test_cancelar_titulo_aberto_cancela_titulo_e_parcelas(self):
        retorno = cancelar_titulo_financeiro(titulo=self.titulo)
        self.titulo.refresh_from_db()
        self.assertEqual(retorno.pk, self.titulo.pk)
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.CANCELADO)
        self.assertFalse(
            self.titulo.parcelas.exclude(status=ParcelaFinanceira.Status.CANCELADO).exists()
        )

    def test_cancelamento_repetido_e_idempotente(self):
        primeiro = cancelar_titulo_financeiro(titulo=self.titulo)
        segundo = cancelar_titulo_financeiro(titulo=self.titulo)
        self.assertEqual(primeiro.pk, segundo.pk)
        self.assertEqual(segundo.status, TituloFinanceiro.Status.CANCELADO)

    def test_nao_cancela_com_saldo_liquido_baixado(self):
        parcela = self.titulo.parcelas.get(numero=1)
        registrar_baixa_financeira(
            parcela=parcela,
            valor=Decimal("20.00"),
            data=date(2026, 9, 14),
            chave_idempotencia="BX-CANCEL-1",
        )
        with self.assertRaises(ValidationError):
            cancelar_titulo_financeiro(titulo=self.titulo)

    def test_pode_cancelar_depois_de_estorno_integral(self):
        parcela = self.titulo.parcelas.get(numero=1)
        baixa = registrar_baixa_financeira(
            parcela=parcela,
            valor=Decimal("20.00"),
            data=date(2026, 9, 14),
            chave_idempotencia="BX-CANCEL-2",
        )
        estornar_baixa_financeira(
            baixa=baixa,
            valor=Decimal("20.00"),
            data=date(2026, 9, 15),
            chave_idempotencia="EST-CANCEL-2",
        )
        cancelar_titulo_financeiro(titulo=self.titulo)
        self.titulo.refresh_from_db()
        self.assertEqual(self.titulo.status, TituloFinanceiro.Status.CANCELADO)

    def test_baixa_em_titulo_cancelado_e_rejeitada(self):
        parcela = self.titulo.parcelas.get(numero=1)
        cancelar_titulo_financeiro(titulo=self.titulo)
        with self.assertRaises(ValidationError):
            registrar_baixa_financeira(
                parcela=parcela,
                valor=Decimal("10.00"),
                data=date(2026, 9, 16),
                chave_idempotencia="BX-POS-CANCEL",
            )