from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

import financeiro.views as financeiro_views


class F2CFluxoCaixaPainelContractTests(TestCase):
    def test_view_importa_selector_fluxo_caixa(self):
        self.assertTrue(
            hasattr(financeiro_views, "resumo_fluxo_caixa"),
            "F2C RED UI: financeiro.views ainda nao importa resumo_fluxo_caixa.",
        )

    def test_view_declara_query_params_e_periodo_padrao_mes_atual(self):
        source = Path(financeiro_views.__file__).read_text(encoding="utf-8")
        self.assertIn('request.GET.get("data_inicio")', source)
        self.assertIn('request.GET.get("data_fim")', source)
        self.assertIn("timezone.localdate()", source)
        self.assertIn("monthrange", source)
        self.assertIn("resumo_fluxo_caixa(", source)

    def test_template_expoe_filtros_e_cards_fluxo(self):
        template = (
            Path(financeiro_views.__file__).resolve().parent
            / "templates"
            / "financeiro"
            / "painel.html"
        ).read_text(encoding="utf-8")
        self.assertIn('name="data_inicio"', template)
        self.assertIn('name="data_fim"', template)
        self.assertIn("Entradas realizadas", template)
        self.assertIn("Saídas realizadas", template)
        self.assertIn("Fluxo líquido realizado", template)
        self.assertIn("Previsto a receber", template)
        self.assertIn("Previsto a pagar", template)
        self.assertIn("Saldo previsto do período", template)