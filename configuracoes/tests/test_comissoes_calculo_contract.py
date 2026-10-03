from decimal import Decimal
from django.test import SimpleTestCase

from configuracoes.services_comissoes import calcular_comissoes_por_metas


class CalculoComissoesContractTests(SimpleTestCase):
    def setUp(self):
        self.metas = [
            {"valor_meta": Decimal("50000.00"), "percentual": Decimal("1.50")},
            {"valor_meta": Decimal("70000.00"), "percentual": Decimal("3.00")},
            {"valor_meta": Decimal("100000.00"), "percentual": Decimal("6.00")},
        ]

    def test_maior_meta_atingida_aplica_percentual_a_todas_vendas_validas_do_vendedor(self):
        resultado = calcular_comissoes_por_metas(
            total_loja=Decimal("82000.00"),
            vendas_por_vendedor={"A": Decimal("18000.00")},
            metas=self.metas,
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        self.assertEqual(resultado.percentual_aplicado, Decimal("3.00"))
        self.assertEqual(resultado.comissoes["A"], Decimal("540.00"))

    def test_vendedor_abaixo_minimo_recebe_zero_quando_regra_ativa(self):
        resultado = calcular_comissoes_por_metas(
            total_loja=Decimal("82000.00"),
            vendas_por_vendedor={"B": Decimal("8000.00")},
            metas=self.metas,
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        self.assertEqual(resultado.comissoes["B"], Decimal("0.00"))

    def test_minimo_individual_e_ignorado_quando_politica_da_matriz_desativada(self):
        resultado = calcular_comissoes_por_metas(
            total_loja=Decimal("82000.00"),
            vendas_por_vendedor={"B": Decimal("8000.00")},
            metas=self.metas,
            exigir_minimo_individual=False,
            minimo_individual=Decimal("10000.00"),
        )
        self.assertEqual(resultado.percentual_aplicado, Decimal("3.00"))
        self.assertEqual(resultado.comissoes["B"], Decimal("240.00"))

    def test_loja_sem_meta_atingida_tem_comissao_zero(self):
        resultado = calcular_comissoes_por_metas(
            total_loja=Decimal("49999.99"),
            vendas_por_vendedor={"A": Decimal("18000.00")},
            metas=self.metas,
            exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        self.assertEqual(resultado.percentual_aplicado, Decimal("0.00"))
        self.assertEqual(resultado.comissoes["A"], Decimal("0.00"))

    def test_quantidade_de_faixas_nao_e_limitada_a_tres(self):
        metas = self.metas + [
            {"valor_meta": Decimal("150000.00"), "percentual": Decimal("8.00")}
        ]
        resultado = calcular_comissoes_por_metas(
            total_loja=Decimal("160000.00"),
            vendas_por_vendedor={"A": Decimal("20000.00")},
            metas=metas,
            exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        self.assertEqual(resultado.percentual_aplicado, Decimal("8.00"))
        self.assertEqual(resultado.comissoes["A"], Decimal("1600.00"))