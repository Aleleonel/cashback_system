from decimal import Decimal
from types import SimpleNamespace
from django.test import SimpleTestCase

from configuracoes.services_comissoes import orquestrar_comissoes_competencia


class OrquestracaoComissoesContractTests(SimpleTestCase):
    def venda(self, vendedor_id, total):
        return SimpleNamespace(vendedor_id=vendedor_id, total=Decimal(total))

    def meta(self, valor, percentual):
        return {"valor_meta": Decimal(valor), "percentual": Decimal(percentual)}

    def test_orquestra_total_loja_agregacao_vendedor_meta_e_minimo(self):
        vendas = [
            self.venda(101, "18000.00"),
            self.venda(102, "8000.00"),
            self.venda(103, "56000.00"),
        ]
        metas = [
            self.meta("50000.00", "1.50"),
            self.meta("70000.00", "3.00"),
            self.meta("100000.00", "6.00"),
        ]
        resultado = orquestrar_comissoes_competencia(
            vendas_validas=vendas,
            metas=metas,
            exigir_minimo_individual=True,
            minimo_individual=Decimal("10000.00"),
        )
        self.assertEqual(resultado.total_loja, Decimal("82000.00"))
        self.assertEqual(resultado.percentual_aplicado, Decimal("3.00"))
        self.assertEqual(resultado.vendas_por_vendedor[101], Decimal("18000.00"))
        self.assertEqual(resultado.vendas_por_vendedor[102], Decimal("8000.00"))
        self.assertEqual(resultado.comissoes[101], Decimal("540.00"))
        self.assertEqual(resultado.comissoes[102], Decimal("0.00"))
        self.assertEqual(resultado.comissoes[103], Decimal("1680.00"))

    def test_orquestra_ignora_minimo_quando_politica_desativada(self):
        resultado = orquestrar_comissoes_competencia(
            vendas_validas=[self.venda(102, "8000.00"), self.venda(103, "74000.00")],
            metas=[self.meta("70000.00", "3.00")],
            exigir_minimo_individual=False,
            minimo_individual=Decimal("10000.00"),
        )
        self.assertEqual(resultado.total_loja, Decimal("82000.00"))
        self.assertEqual(resultado.comissoes[102], Decimal("240.00"))

    def test_orquestra_sem_meta_atingida_retorna_percentual_e_comissoes_zero(self):
        resultado = orquestrar_comissoes_competencia(
            vendas_validas=[self.venda(101, "10000.00")],
            metas=[self.meta("50000.00", "1.50")],
            exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        self.assertEqual(resultado.total_loja, Decimal("10000.00"))
        self.assertEqual(resultado.percentual_aplicado, Decimal("0.00"))
        self.assertEqual(resultado.comissoes[101], Decimal("0.00"))