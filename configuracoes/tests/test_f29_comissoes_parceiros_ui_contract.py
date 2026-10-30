from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]
VIEWS = (ROOT / "configuracoes" / "views.py").read_text(encoding="utf-8")
TPL = (ROOT / "configuracoes" / "templates" / "configuracoes" / "comissoes.html").read_text(encoding="utf-8")


class F29ComissoesParceirosUIContractTests(SimpleTestCase):
    def test_view_carrega_comissoes_parceiros_da_matriz_e_titulos_namespace_parceiro(self):
        inicio = VIEWS.index("def comissoes(request):")
        fim = VIEWS.index("def meta_comissao_editar", inicio)
        bloco = VIEWS[inicio:fim]
        self.assertIn("ComissaoParceiro", bloco)
        self.assertIn("comissoes_parceiros", bloco)
        self.assertIn("PARCEIRO:", bloco)
        self.assertIn("COMISSAO_PARCEIRO:", bloco)

    def test_view_tem_acao_financeira_especifica_para_parceiro(self):
        inicio = VIEWS.index("def comissoes(request):")
        fim = VIEWS.index("def meta_comissao_editar", inicio)
        bloco = VIEWS[inicio:fim]
        self.assertIn('provisionar_comissao_parceiro', bloco)
        self.assertIn("gerar_titulo_financeiro_comissao_parceiro", bloco)

    def test_template_separa_vendedores_e_parceiros_sem_misturar_regras(self):
        self.assertIn("Vendedores", TPL)
        self.assertIn("Parceiros", TPL)
        self.assertIn("comissoes_parceiros", TPL)
        self.assertIn('value="provisionar_comissao_parceiro"', TPL)

    def test_template_parceiros_expoe_metricas_do_snapshot_e_uso(self):
        for termo in (
            "valor_compra",
            "valor_desconto",
            "valor_base",
            "valor_comissao",
            "parceiro",
        ):
            self.assertIn(termo, TPL)