from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent

class DREApresentacaoContratoRedTests(SimpleTestCase):
    def _ler(self, relativo):
        p = ROOT / relativo
        self.assertTrue(p.exists(), f"Arquivo obrigatorio ausente: {relativo}")
        return p.read_text(encoding="utf-8")

    def test_view_dre_usa_api_gerencial_e_competencia(self):
        src=self._ler("relatorios/views.py")
        for token in ("def dre(", "apurar_dre", "data_inicio", "data_fim", "REGIME_COMPETENCIA"):
            self.assertIn(token, src)

    def test_view_dre_respeita_escopo_matriz_loja_e_centro_custo(self):
        src=self._ler("relatorios/views.py")
        for token in ("get_contexto_operacional_usuario", "loja", "centro_custo", "operador"):
            self.assertIn(token, src)
        self.assertIn("def dre(", src)

    def test_urls_dre_incluem_tela_pdf_xlsx(self):
        src=self._ler("relatorios/urls.py")
        for token in ("dre/", "dre/pdf/", "dre/xlsx/", "name='dre'", "exportar_dre_pdf", "exportar_dre_xlsx"):
            self.assertIn(token, src)

    def test_template_dre_expoe_filtros_e_regime(self):
        src=self._ler("relatorios/templates/relatorios/dre.html")
        for token in ("Demonstra", "Compet", "data_inicio", "data_fim", "loja", "centro_custo"):
            self.assertIn(token, src)

    def test_template_dre_expoe_estrutura_gerencial_e_analise_vertical(self):
        src=self._ler("relatorios/templates/relatorios/dre.html")
        for token in ("Receita Bruta", "Dedu", "Receita L", "CMV", "Lucro Bruto", "Despesas Operacionais", "Resultado Operacional", "Resultado Financeiro", "Outras Receitas", "Resultado Antes", "analise_vertical"):
            self.assertIn(token, src)

    def test_template_dre_expoe_comparativo_e_evolucao(self):
        src=self._ler("relatorios/templates/relatorios/dre.html")
        for token in ("comparativo", "evolucao", "Per", "Varia"):
            self.assertIn(token, src)

    def test_template_dre_expoe_drilldown_e_exportacoes(self):
        src=self._ler("relatorios/templates/relatorios/dre.html")
        for token in ("drilldown", "PDF", "Excel", "exportar_dre_pdf", "exportar_dre_xlsx"):
            self.assertIn(token, src)

    def test_view_dre_protegida_por_permissao_existente(self):
        src=self._ler("relatorios/views.py")
        pos=src.find("def dre(")
        self.assertGreaterEqual(pos,0)
        trecho=src[max(0,pos-300):pos]
        self.assertIn("@login_required", trecho)
        self.assertIn("@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)", trecho)