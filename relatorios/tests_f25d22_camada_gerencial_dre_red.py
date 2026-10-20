from datetime import date
from decimal import Decimal
from django.test import SimpleTestCase

from relatorios import services_dre


class F25D22CamadaGerencialDRERedTests(SimpleTestCase):
    """
    Contrato RED da camada gerencial.
    Nao testa HTML/UI: congela apenas a API de servico que depois alimentara
    view, comparativos, exportacoes e drill-down.
    """

    def test_apurar_dre_existe_como_orquestrador_publico(self):
        self.assertTrue(
            hasattr(services_dre, "apurar_dre"),
            "Falta apurar_dre como API publica/orquestradora da DRE.",
        )

    def test_analise_vertical_existe_e_preserva_base_receita_liquida(self):
        self.assertTrue(
            hasattr(services_dre, "calcular_analise_vertical"),
            "Falta calcular_analise_vertical.",
        )

    def test_comparar_periodos_existe(self):
        self.assertTrue(
            hasattr(services_dre, "comparar_periodos"),
            "Falta comparar_periodos.",
        )

    def test_evolucao_mensal_existe(self):
        self.assertTrue(
            hasattr(services_dre, "apurar_evolucao_mensal"),
            "Falta apurar_evolucao_mensal.",
        )

    def test_drilldown_existe_e_e_rastreavel(self):
        self.assertTrue(
            hasattr(services_dre, "obter_drilldown_dre"),
            "Falta obter_drilldown_dre.",
        )

    def test_contrato_comparativo_tem_atual_anterior_variacao(self):
        cls=getattr(services_dre,"ComparativoDRE",None)
        self.assertIsNotNone(cls,"Falta contrato ComparativoDRE.")
        campos=set(getattr(cls,"__dataclass_fields__",{}))
        self.assertTrue(
            {"atual","anterior","variacao_absoluta","variacao_percentual"}.issubset(campos),
            f"Campos insuficientes em ComparativoDRE: {sorted(campos)}",
        )

    def test_contrato_drilldown_nao_depende_de_nome_textual_de_conta(self):
        codigo=(__import__("pathlib").Path(services_dre.__file__).read_text(encoding="utf-8"))
        self.assertIn("classificacao_dre",codigo)
        self.assertNotIn('nome__icontains',codigo)
        self.assertNotIn('codigo__startswith',codigo)