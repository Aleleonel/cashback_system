from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "financeiro" / "templates" / "financeiro" / "titulo_detalhe.html"
VIEWS = ROOT / "financeiro" / "views.py"


class R13RastreabilidadeBaixasDetalheRedTests(SimpleTestCase):
    def test_tabela_expoe_forma_pagamento_e_conta_financeira(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("Forma de pagamento", source)
        self.assertIn("Conta financeira", source)
        self.assertIn("baixa.forma_pagamento", source)
        self.assertIn("baixa.conta_financeira", source)

    def test_fallback_preserva_baixas_historicas_sem_referencias(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('baixa.forma_pagamento|default:"-"', source)
        self.assertIn('baixa.conta_financeira|default:"-"', source)

    def test_tabela_vazia_usa_seis_colunas(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn('colspan="7"', source)

    def test_view_prefetch_carrega_relacoes_da_baixa(self):
        source = VIEWS.read_text(encoding="utf-8")
        self.assertIn("Prefetch", source)
        self.assertIn('select_related("forma_pagamento", "conta_financeira")', source)