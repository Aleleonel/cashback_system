from decimal import Decimal

from django.core.exceptions import ValidationError

from financeiro.models import BaixaFinanceira
from financeiro.services import estornar_baixa_financeira, registrar_baixa_financeira
from financeiro.tests_services_estorno_baixa import EstornarBaixaFinanceiraContratoTests


class R14AssociacaoEstornoServiceTests(EstornarBaixaFinanceiraContratoTests):
    def test_estorno_criado_aponta_para_baixa_original(self):
        estorno = estornar_baixa_financeira(
            baixa=self.baixa,
            valor=Decimal("10.00"),
            data=self.baixa.data,
            chave_idempotencia="r14-assoc-estorno",
        )
        self.assertEqual(estorno.baixa_estornada_id, self.baixa.pk)
        self.assertEqual(estorno.tipo, BaixaFinanceira.Tipo.ESTORNO)

    def test_limite_considera_baixa_selecionada_e_nao_liquido_global_parcela(self):
        segunda_baixa = registrar_baixa_financeira(
            parcela=self.parcela,
            valor=Decimal("20.00"),
            data=self.baixa.data,
            chave_idempotencia="r14-limite-baixa2",
            observacao="Segunda baixa",
        )
        self.assertNotEqual(segunda_baixa.pk, self.baixa.pk)

        estornar_baixa_financeira(
            baixa=self.baixa,
            valor=Decimal("20.00"),
            data=self.baixa.data,
            chave_idempotencia="r14-limite-estorno1",
        )
        antes = BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count()

        with self.assertRaises(ValidationError):
            estornar_baixa_financeira(
                baixa=self.baixa,
                valor=Decimal("20.01"),
                data=self.baixa.data,
                chave_idempotencia="r14-limite-estorno2",
            )

        depois = BaixaFinanceira.objects.filter(tipo=BaixaFinanceira.Tipo.ESTORNO).count()
        self.assertEqual(depois, antes)