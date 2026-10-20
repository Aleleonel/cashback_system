from pathlib import Path
from django.test import SimpleTestCase

ROOT=Path(__file__).resolve().parents[1]
CODIGO=(ROOT/"relatorios"/"services_dre.py").read_text(encoding="utf-8")


class F25D19ContratosSemanticosDRERedTests(SimpleTestCase):
    """
    RED documental/estrutural dos tres contratos que ainda precisam ficar
    explicitos antes de expandir a DRE para UI, comparativos e exportacoes.
    """

    def test_dre_declara_contrato_de_sinal_sem_abs_e_reversao_implicita(self):
        self.assertIn("CONTRATO_SINAL_DRE", CODIGO)
        self.assertIn("REVERSAO_DRE_EXPLICITA", CODIGO)
        self.assertNotIn("deducoes_financeiras += abs(valor)", CODIGO)
        self.assertNotIn("despesas_operacionais += abs(valor)", CODIGO)

    def test_centro_custo_nao_promete_dre_completa_sem_atribuicao_venda_cmv(self):
        self.assertIn("ESCOPO_CENTRO_CUSTO_DRE", CODIGO)
        self.assertIn("APENAS_LANCAMENTOS_CLASSIFICADOS", CODIGO)
        self.assertIn("CENTRO_CUSTO_NAO_FILTRA_VENDAS_CMV_COMISSOES", CODIGO)

    def test_periodo_parcial_nao_inclui_comissao_mensal_integral(self):
        self.assertIn("COMPETENCIA_COMISSAO_MES_FECHADO", CODIGO)
        self.assertIn("PERIODO_PARCIAL_EXCLUI_COMISSAO_MENSAL", CODIGO)
        self.assertIn("inicio.day == 1", CODIGO)
        self.assertIn("fim.day", CODIGO)