from pathlib import Path

from django.test import SimpleTestCase


class ProntidaoFiscalLoja195CFG3BTests(SimpleTestCase):
    def test_selector_evitar_n_mais_um(self):
        source = (Path(__file__).resolve().parent / "selectors.py").read_text(encoding="utf-8")
        self.assertIn('select_related("configuracao_emissao_fiscal")', source)

    def test_view_delega_prontidao_ao_servico_central(self):
        source = (Path(__file__).resolve().parent / "views" / "lojas.py").read_text(encoding="utf-8")
        self.assertIn("avaliar_prontidao_fiscal_loja(loja)", source)
        self.assertIn('prontidao_fiscal_status = prontidao["status"]', source)
        self.assertIn('prontidao_fiscal_label = prontidao["label"]', source)
        self.assertIn('prontidao_fiscal_detalhe = prontidao["detalhe"]', source)

    def test_template_exibe_coluna_fiscal(self):
        source = (Path(__file__).resolve().parent / "templates" / "empresa" / "lista_lojas.html").read_text(encoding="utf-8")
        self.assertIn("Fiscal NFC-e", source)
        self.assertIn("prontidao_fiscal_label", source)
        self.assertIn('== "configurada"', source)
        self.assertIn('== "inativa"', source)
