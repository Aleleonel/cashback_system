from pathlib import Path
from django.test import SimpleTestCase


class F2EA22ComissoesRenderSnapshotTests(SimpleTestCase):
    def test_template_usa_campos_reais_do_snapshot(self):
        caminho = Path(__file__).resolve().parent / "templates" / "relatorios" / "relatorio_comissoes.html"
        fonte = caminho.read_text(encoding="utf-8")
        self.assertIn("item.fechamento.total_vendas_loja", fonte)
        self.assertIn("item.fechamento.valor_meta_atingida", fonte)
        self.assertIn("item.total_vendas_vendedor", fonte)
        self.assertIn("item.valor_comissao", fonte)
        self.assertNotIn("item.fechamento.meta_atingida_valor", fonte)
        self.assertNotIn("item.total_vendas|", fonte)