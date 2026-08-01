from pathlib import Path
from django.test import SimpleTestCase


class PdvSessaoCaixaUnicaContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.models = Path("pdv/models.py").read_text(encoding="utf-8")
        cls.service = Path("pdv/services/vendas/caixa.py").read_text(encoding="utf-8")
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")

    def test_constraint_por_operador(self):
        self.assertIn("uq_pdv_uma_sessao_aberta_por_operador", self.models)
        self.assertIn('fields=["operador_abertura"]', self.models)

    def test_service_transacional(self):
        self.assertIn("def abrir_sessao_caixa(", self.service)
        self.assertIn("select_for_update()", self.service)
        self.assertIn("O operador ja possui uma sessao", self.service)

    def test_view_usa_service(self):
        self.assertIn(
            "from pdv.services.vendas.caixa import abrir_sessao_caixa",
            self.views,
        )
        self.assertIn("sessao = abrir_sessao_caixa(", self.views)

    def test_contexto_e_fechamento_filtram_operador(self):
        self.assertGreaterEqual(
            self.views.count("operador_abertura=request.user"),
            2,
        )
        inicio = self.views.index(
            "def _pdv04c1_sessao_aberta_do_usuario(request):"
        )
        trecho = self.views[inicio:inicio + 1200]
        self.assertNotIn("Ha mais de uma sessao aberta", trecho)
