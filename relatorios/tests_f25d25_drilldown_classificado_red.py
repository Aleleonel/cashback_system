from decimal import Decimal
from django.test import SimpleTestCase
from relatorios.services_dre import ResultadoDRE, obter_drilldown_dre

D=Decimal

def resultado(memoria):
    return ResultadoDRE(
        receita_bruta=D("0"), acrescimos=D("0"), deducoes_receita=D("0"),
        receita_liquida=D("0"), cmv=D("0"), lucro_bruto=D("0"),
        despesas_operacionais=D("0"), resultado_operacional=D("0"),
        resultado_financeiro=D("0"), outras_receitas_despesas=D("0"),
        resultado_antes_impostos=D("0"), margem_bruta=D("0"),
        margem_operacional=D("0"), memoria_calculo=memoria,
    )

class F25D25DrilldownClassificadoRedTests(SimpleTestCase):
    def setUp(self):
        self.r=resultado({
            "origens_receita":[1],
            "origens_cmv":[2],
            "origens_despesas":{"titulos":[10,20,30,40],"comissoes":[50]},
            "origens_por_linha":{
                "deducoes_receita":{"titulos":[10]},
                "despesas_operacionais":{"titulos":[20],"comissoes":[50]},
                "resultado_financeiro":{"titulos":[30]},
                "outras_receitas_despesas":{"titulos":[40]},
            },
        })

    def test_deducao_expoe_somente_titulos_da_linha(self):
        self.assertEqual(obter_drilldown_dre(self.r,"deducoes_receita"),{"vendas":[1],"titulos":[10]})

    def test_despesa_operacional_nao_vaza_financeiro_ou_outros(self):
        self.assertEqual(obter_drilldown_dre(self.r,"despesas_operacionais"),{"titulos":[20],"comissoes":[50]})

    def test_resultado_financeiro_nao_vaza_despesas_operacionais(self):
        self.assertEqual(obter_drilldown_dre(self.r,"resultado_financeiro"),{"titulos":[30]})

    def test_outras_receitas_despesas_nao_vaza_demais_titulos(self):
        self.assertEqual(obter_drilldown_dre(self.r,"outras_receitas_despesas"),{"titulos":[40]})

    def test_memoria_classificada_e_contrato_obrigatorio(self):
        self.assertIn("origens_por_linha",self.r.memoria_calculo)