from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
URLS = ROOT / "financeiro" / "urls.py"
VIEWS = ROOT / "financeiro" / "views.py"
FORMS = ROOT / "financeiro" / "forms.py"
DETALHE = ROOT / "financeiro" / "templates" / "financeiro" / "titulo_detalhe.html"


class R14EstornoUiRedTests(SimpleTestCase):
    def test_rota_estorno_por_titulo_parcela_e_baixa(self):
        source = URLS.read_text(encoding="utf-8")
        self.assertIn('baixas/<int:baixa_id>/estornar/', source)
        self.assertIn('name="baixa_estornar"', source)

    def test_view_exige_permissao_escopo_e_servico_integrado(self):
        source = VIEWS.read_text(encoding="utf-8")
        self.assertIn("def baixa_estornar(", source)
        self.assertIn("@require_permission(PERMISSAO_FINANCEIRO_BAIXAR)", source)
        self.assertIn("_lojas_autorizadas(request, matriz)", source)
        self.assertIn("estornar_baixa_financeira_com_caixa", source)
        self.assertIn("BaixaFinanceira.Tipo.BAIXA", source)

    def test_form_estorno_tem_somente_valor_data_observacao(self):
        source = FORMS.read_text(encoding="utf-8")
        self.assertIn("class EstornoBaixaForm(forms.Form):", source)
        self.assertIn("valor = forms.DecimalField", source)
        self.assertIn("data = forms.DateField", source)
        self.assertIn("observacao = forms.CharField", source)
        bloco = source.split("class EstornoBaixaForm(forms.Form):", 1)[1]
        bloco = bloco.split("\nclass ", 1)[0]
        self.assertNotIn("forma_pagamento", bloco)
        self.assertNotIn("conta_financeira", bloco)
        self.assertIn('format="%Y-%m-%d"', bloco)

    def test_detalhe_oferece_acao_estornar(self):
        source = DETALHE.read_text(encoding="utf-8")
        self.assertIn("financeiro:baixa_estornar", source)
        self.assertIn("Estornar", source)

    def test_view_preserva_token_idempotencia_e_retorna_ao_detalhe(self):
        source = VIEWS.read_text(encoding="utf-8")
        self.assertIn("chave_idempotencia", source)
        self.assertIn("estorno-ui:", source)
        self.assertIn('"financeiro:titulo_detalhe"', source)