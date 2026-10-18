from pathlib import Path
from django.test import SimpleTestCase

class F24ExtratoFinanceiroCompletoRED(SimpleTestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parent
        self.views=(self.root/"views.py").read_text(encoding="utf-8")
        self.urls=(self.root/"urls.py").read_text(encoding="utf-8")
        self.tpl=(self.root/"templates"/"financeiro"/"conta_financeira_extrato.html").read_text(encoding="utf-8")
        p=self.views.index("def _extrato_conta_contexto(")
        n=self.views.find("\ndef ",p+4)
        self.view=self.views[p:n if n!=-1 else None]

    def test_filtros_periodo_tipo_natureza_forma_busca(self):
        for token in ("data_inicio","data_fim","tipo","natureza","forma_pagamento","busca"):
            self.assertIn(token,self.view)

    def test_totais_periodo(self):
        for token in ("total_entradas","total_saidas","saldo_liquido","total_movimentacoes"):
            self.assertIn(token,self.view)

    def test_paginacao_preserva_querystring(self):
        self.assertIn("querystring",self.tpl)
        self.assertIn("page=",self.tpl)

    def test_template_expoe_filtros_e_resumo(self):
        for token in ('name="data_inicio"','name="data_fim"','name="tipo"','name="natureza"','name="forma_pagamento"','name="busca"'):
            self.assertIn(token,self.tpl)
        for texto in ("Entradas","Sa&iacute;das","Saldo l&iacute;quido","Movimenta&ccedil;&otilde;es"):
            self.assertIn(texto,self.tpl)

    def test_pdf_tem_rota_e_view(self):
        self.assertIn("conta_financeira_extrato_pdf",self.urls)
        self.assertIn("def conta_financeira_extrato_pdf(",self.views)

    def test_pdf_reutiliza_filtros_e_reportlab(self):
        p=self.views.index("def conta_financeira_extrato_pdf(") if "def conta_financeira_extrato_pdf(" in self.views else 0
        trecho=self.views[p:p+5000]
        self.assertIn("reportlab",self.views.lower())
        self.assertIn("_extrato_conta_contexto",trecho)
        helper_inicio=self.views.index("def _extrato_conta_contexto(")
        helper_fim=self.views.find("\ndef ",helper_inicio+4)
        helper=self.views[helper_inicio:helper_fim if helper_fim!=-1 else None]
        for token in ("data_inicio","data_fim","tipo","natureza","forma_pagamento","busca"):
            self.assertIn(token,helper)

    def test_sem_novo_ledger(self):
        models=(self.root/"models.py").read_text(encoding="utf-8")
        self.assertNotIn("class ExtratoContaFinanceira(",models)
        self.assertNotIn("class MovimentacaoFinanceira(",models)