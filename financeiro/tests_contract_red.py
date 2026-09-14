from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent

class FundacaoFinanceiraContractRedTests(SimpleTestCase):
    def test_app_financeiro_deve_existir(self):
        self.assertTrue((ROOT / "financeiro" / "apps.py").exists())

    def test_models_fundacao_devem_existir(self):
        models = ROOT / "financeiro" / "models.py"
        self.assertTrue(models.exists())
        texto = models.read_text(encoding="utf-8")
        self.assertIn("class TituloFinanceiro", texto)
        self.assertIn("class ParcelaFinanceira", texto)
        self.assertIn("class BaixaFinanceira", texto)

    def test_fundacao_deve_expor_servicos(self):
        services = ROOT / "financeiro" / "services.py"
        self.assertTrue(services.exists())

    def test_fundacao_deve_expor_selectors(self):
        selectors = ROOT / "financeiro" / "selectors.py"
        self.assertTrue(selectors.exists())