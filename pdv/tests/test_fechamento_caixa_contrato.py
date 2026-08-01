from pathlib import Path
from django.test import SimpleTestCase


class FechamentoCaixaContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]
        cls.service = (root / "pdv/services/vendas/caixa.py").read_text(encoding="utf-8")
        cls.views = (root / "pdv/views.py").read_text(encoding="utf-8")
        cls.urls = (root / "pdv/urls.py").read_text(encoding="utf-8")
        cls.template = (
            root / "pdv/templates/pdv/fechar_caixa.html"
        ).read_text(encoding="utf-8")

    def test_service_e_transacional(self):
        self.assertIn("def fechar_sessao_caixa(", self.service)
        self.assertIn("transaction.atomic", self.service)
        self.assertIn("select_for_update", self.service)

    def test_service_bloqueia_vendas_pendentes(self):
        self.assertIn("vendas_pendentes", self.service)
        self.assertIn("StatusOperacaoVenda.FINALIZADA", self.service)
        self.assertIn("StatusOperacaoVenda.CANCELADA", self.service)

    def test_service_registra_valores_e_movimento(self):
        self.assertIn("valor_fechamento_informado", self.service)
        self.assertIn("valor_fechamento_calculado", self.service)
        self.assertIn("diferenca_fechamento", self.service)
        self.assertIn("TipoMovimentacaoCaixa.FECHAMENTO", self.service)

    def test_views_get_e_post_existem(self):
        self.assertIn("def fechar_caixa(", self.views)
        self.assertIn("def confirmar_fechamento_caixa(", self.views)
        self.assertIn("PERMISSAO_PDV_FECHAR_CAIXA", self.views)

    def test_rotas_nomeadas_existem(self):
        self.assertIn('name="fechar_caixa"', self.urls)
        self.assertIn('name="confirmar_fechamento_caixa"', self.urls)

    def test_template_tem_csrf_e_campos(self):
        self.assertIn("{% csrf_token %}", self.template)
        self.assertIn('name="valor_fechamento"', self.template)
        self.assertIn('name="observacao_fechamento"', self.template)
