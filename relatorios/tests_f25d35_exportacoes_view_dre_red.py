from pathlib import Path
from django.test import SimpleTestCase

ROOT=Path(__file__).resolve().parent.parent

class DREExportacoesViewHardeningRedTests(SimpleTestCase):
    def _ler(self,rel):
        p=ROOT/rel
        self.assertTrue(p.exists(),f"Arquivo ausente: {rel}")
        return p.read_text(encoding="utf-8")

    def test_pdf_dre_e_binario_real_com_disposition(self):
        s=self._ler("relatorios/views.py")
        trecho=s[s.find("def exportar_dre_pdf"):s.find("def exportar_dre_xlsx")]
        for token in ("BytesIO","SimpleDocTemplate","application/pdf","Content-Disposition","relatorio_dre.pdf","doc.build"):
            self.assertIn(token,trecho)
        self.assertNotIn("pendente de hardening",trecho)

    def test_xlsx_dre_e_binario_real_com_disposition(self):
        s=self._ler("relatorios/views.py")
        trecho=s[s.find("def exportar_dre_xlsx"):]
        for token in ("BytesIO","Workbook","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","Content-Disposition","relatorio_dre.xlsx","wb.save"):
            self.assertIn(token,trecho)
        self.assertNotIn("pendente de hardening",trecho)

    def test_exportacoes_reutilizam_mesmo_contexto_e_filtros_da_tela(self):
        s=self._ler("relatorios/views.py")
        for nome in ("def exportar_dre_pdf","def exportar_dre_xlsx"):
            i=s.find(nome);self.assertGreaterEqual(i,0)
            trecho=s[i:i+2500]
            self.assertIn("_contexto_dre(request)",trecho)

    def test_template_preserva_selecao_loja_e_centro_custo(self):
        s=self._ler("relatorios/templates/relatorios/dre.html")
        self.assertIn("loja_filtro",s)
        self.assertIn("centro_custo_filtro",s)
        self.assertIn("selected",s)

    def test_template_nao_expoe_dict_bruto_como_drilldown(self):
        s=self._ler("relatorios/templates/relatorios/dre.html")
        for token in ("{{ drilldown.receita_bruta }}","{{ drilldown.deducoes_receita }}","{{ comparativo }}"):
            self.assertNotIn(token,s)

    def test_template_formata_valores_monetarios_e_percentuais(self):
        s=self._ler("relatorios/templates/relatorios/dre.html")
        self.assertIn("R$ ",s)
        self.assertIn("floatformat:2",s)

    def test_template_tem_limpar_e_impressao(self):
        s=self._ler("relatorios/templates/relatorios/dre.html")
        for token in ("Limpar","window.print","Imprimir"):
            self.assertIn(token,s)

    def test_view_mantem_protecao_e_regime_competencia(self):
        s=self._ler("relatorios/views.py")
        i=s.find("def dre(");self.assertGreaterEqual(i,0)
        self.assertIn("@login_required",s[max(0,i-300):i])
        self.assertIn("@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)",s[max(0,i-300):i])
        self.assertIn("REGIME_COMPETENCIA",s)