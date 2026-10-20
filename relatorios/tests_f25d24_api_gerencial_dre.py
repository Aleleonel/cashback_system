from dataclasses import replace
from datetime import date
from decimal import Decimal
from django.test import SimpleTestCase
from relatorios.services_dre import (
    ResultadoDRE, calcular_analise_vertical, comparar_periodos,
    apurar_evolucao_mensal, obter_drilldown_dre, apurar_dre,
)
from unittest.mock import patch

D=Decimal

def resultado(**kw):
    base=dict(
        receita_bruta=D("200"), acrescimos=D("10"), deducoes_receita=D("20"),
        receita_liquida=D("190"), cmv=D("80"), lucro_bruto=D("110"),
        despesas_operacionais=D("40"), resultado_operacional=D("70"),
        resultado_financeiro=D("5"), outras_receitas_despesas=D("0"),
        resultado_antes_impostos=D("75"), margem_bruta=D("0"),
        margem_operacional=D("0"),
        memoria_calculo={
            "origens_receita":[7],
            "origens_cmv":[11],
            "origens_despesas":{"titulos":[21,22],"comissoes":[31]},
            "origens_por_linha":{
                "deducoes_receita":{"titulos":[]},
                "despesas_operacionais":{"titulos":[21,22],"comissoes":[31]},
                "resultado_financeiro":{"titulos":[]},
                "outras_receitas_despesas":{"titulos":[]},
            },
        },
    )
    base.update(kw)
    return ResultadoDRE(**base)

class F25D24APIGerencialDRETests(SimpleTestCase):
    def test_analise_vertical_usa_receita_liquida_como_base(self):
        av=calcular_analise_vertical(resultado())
        self.assertEqual(av["receita_liquida"],D("100.00"))
        self.assertEqual(av["cmv"],D("80")/D("190")*D("100.00"))
        self.assertEqual(av["resultado_antes_impostos"],D("75")/D("190")*D("100.00"))

    def test_analise_vertical_receita_liquida_zero_nao_divide_por_zero(self):
        av=calcular_analise_vertical(resultado(receita_liquida=D("0")))
        self.assertTrue(all(v==D("0") for v in av.values()))

    @patch("relatorios.services_dre.calcular_dre")
    def test_comparativo_calcula_variacao_e_trata_base_zero(self,m):
        atual=resultado(receita_bruta=D("150"),receita_liquida=D("120"))
        anterior=resultado(receita_bruta=D("100"),receita_liquida=D("0"))
        m.side_effect=[atual,anterior]
        c=comparar_periodos(matriz=object(),inicio=date(2026,10,1),fim=date(2026,10,31),inicio_anterior=date(2026,9,1),fim_anterior=date(2026,9,30))
        self.assertEqual(c.variacao_absoluta["receita_bruta"],D("50"))
        self.assertEqual(c.variacao_percentual["receita_bruta"],D("50.00"))
        self.assertIsNone(c.variacao_percentual["receita_liquida"])

    @patch("relatorios.services_dre.calcular_dre")
    def test_evolucao_mensal_respeita_limites_parciais(self,m):
        m.return_value=resultado()
        pontos=apurar_evolucao_mensal(matriz=object(),inicio=date(2026,9,15),fim=date(2026,11,20))
        self.assertEqual([(p["inicio"],p["fim"]) for p in pontos],[
            (date(2026,9,15),date(2026,9,30)),
            (date(2026,10,1),date(2026,10,31)),
            (date(2026,11,1),date(2026,11,20)),
        ])
        self.assertEqual(m.call_count,3)

    def test_drilldown_retorna_ids_reconciliaveis(self):
        r=resultado()
        self.assertEqual(obter_drilldown_dre(r,"receita_bruta"),{"vendas":[7]})
        self.assertEqual(obter_drilldown_dre(r,"cmv"),{"itens_venda":[11]})
        self.assertEqual(obter_drilldown_dre(r,"despesas_operacionais"),{"titulos":[21,22],"comissoes":[31]})

    @patch("relatorios.services_dre.calcular_dre")
    def test_apurar_dre_orquestra_resultado_vertical_e_drilldown(self,m):
        r=resultado();m.return_value=r
        a=apurar_dre(matriz=object(),inicio=date(2026,10,1),fim=date(2026,10,31))
        self.assertIs(a["resultado"],r)
        self.assertEqual(a["analise_vertical"]["receita_liquida"],D("100.00"))
        self.assertEqual(a["drilldown"]["receita_bruta"],{"vendas":[7]})