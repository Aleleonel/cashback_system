from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent

class R16EdicaoContaFinanceiraRedTests(SimpleTestCase):
    def test_rota_edicao_existe(self):
        texto=(ROOT/"urls.py").read_text(encoding="utf-8")
        self.assertIn('contas-financeiras/<uuid:conta_uuid>/editar/', texto)
        self.assertIn('name="conta_financeira_editar"', texto)

    def test_view_edicao_existe_com_permissao_e_escopo(self):
        texto=(ROOT/"views.py").read_text(encoding="utf-8")
        self.assertIn("def conta_financeira_editar(request, conta_uuid):", texto)
        inicio=texto.index("def conta_financeira_editar(request, conta_uuid):")
        trecho=texto[max(0,inicio-180):inicio+1800]
        self.assertIn("PERMISSAO_FINANCEIRO_GERENCIAR", trecho)
        self.assertIn("matriz=matriz", trecho)
        self.assertIn("instance=conta", trecho)
        self.assertIn('_lojas_autorizadas(request, matriz)', trecho)
        self.assertIn('return redirect("financeiro:contas_financeiras")', trecho)

    def test_listagem_expoe_acao_editar(self):
        texto=(ROOT/"templates"/"financeiro"/"contas_financeiras.html").read_text(encoding="utf-8")
        self.assertIn("financeiro:conta_financeira_editar", texto)
        self.assertIn("Editar", texto)

    def test_form_reutilizado_distingue_edicao(self):
        texto=(ROOT/"templates"/"financeiro"/"conta_financeira_form.html").read_text(encoding="utf-8")
        self.assertIn("conta", texto)
        self.assertIn("Editar", texto)