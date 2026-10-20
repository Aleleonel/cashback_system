from decimal import Decimal
from django.test import SimpleTestCase
from relatorios.services_dre import ResultadoDRE, obter_drilldown_dre

class F25D28DrilldownLinhasDerivadasRedTests(SimpleTestCase):
    def setUp(self):
        self.r=ResultadoDRE(
            receita_bruta=Decimal("210"),acrescimos=Decimal("10"),deducoes_receita=Decimal("20"),
            receita_liquida=Decimal("190"),cmv=Decimal("80"),lucro_bruto=Decimal("110"),
            despesas_operacionais=Decimal("40"),resultado_operacional=Decimal("70"),
            resultado_financeiro=Decimal("5"),outras_receitas_despesas=Decimal("0"),
            resultado_antes_impostos=Decimal("75"),margem_bruta=Decimal("0"),margem_operacional=Decimal("0"),
            memoria_calculo={"origens_receita":[1],"origens_cmv":[2],"origens_despesas":{"titulos":[10,20,30,40],"comissoes":[50]},
            "origens_por_linha":{"deducoes_receita":{"titulos":[10]},"despesas_operacionais":{"titulos":[20],"comissoes":[50]},
            "resultado_financeiro":{"titulos":[30]},"outras_receitas_despesas":{"titulos":[40]}}})
    def test_receita_liquida_expoe_formula_e_componentes(self):
        self.assertEqual(obter_drilldown_dre(self.r,"receita_liquida"),{"tipo":"DERIVADO","formula":"receita_bruta - deducoes_receita","componentes":["receita_bruta","deducoes_receita"]})
    def test_lucro_bruto_expoe_formula_e_componentes(self):
        self.assertEqual(obter_drilldown_dre(self.r,"lucro_bruto"),{"tipo":"DERIVADO","formula":"receita_liquida - cmv","componentes":["receita_liquida","cmv"]})
    def test_resultado_operacional_expoe_formula_e_componentes(self):
        self.assertEqual(obter_drilldown_dre(self.r,"resultado_operacional"),{"tipo":"DERIVADO","formula":"lucro_bruto - despesas_operacionais","componentes":["lucro_bruto","despesas_operacionais"]})
    def test_resultado_antes_impostos_expoe_formula_e_componentes(self):
        self.assertEqual(obter_drilldown_dre(self.r,"resultado_antes_impostos"),{"tipo":"DERIVADO","formula":"resultado_operacional + resultado_financeiro + outras_receitas_despesas","componentes":["resultado_operacional","resultado_financeiro","outras_receitas_despesas"]})