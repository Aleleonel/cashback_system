from pathlib import Path
from django.test import SimpleTestCase

class R15JCorrecaoEscopoCancelamentoRedTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.views = Path("financeiro/views.py").read_text(encoding="utf-8")
        cls.detail = Path("financeiro/templates/financeiro/titulo_detalhe.html").read_text(encoding="utf-8")
        cls.confirm = Path("financeiro/templates/financeiro/titulo_cancelar_confirm.html").read_text(encoding="utf-8")

    def _cancel_block(self):
        start = self.views.index("def titulo_cancelar(")
        end = self.views.index("\ndef ", start + 5)
        return self.views[start:end]

    def test_cancelamento_deve_resolver_mesmo_escopo_do_detalhe(self):
        block = self._cancel_block()
        self.assertIn("_resolver_escopo(request, matriz)", block)
        self.assertIn("ESCOPO_MATRIZ", block)
        self.assertIn("ESCOPO_LOJA", block)
        self.assertIn("loja__isnull=True", block)
        self.assertIn("queryset.filter(loja=loja)", block)

    def test_cancelamento_nao_deve_rejeitar_incondicionalmente_titulo_matriz(self):
        block = self._cancel_block()
        self.assertNotIn("titulo.loja_id is None or", block)
        self.assertNotIn("Titulo sem loja autorizada para cancelamento.", block)

    def test_link_cancelar_deve_preservar_escopo_atual(self):
        self.assertIn("?escopo={{ escopo }}", self.detail)
        self.assertIn("&loja={{ loja.pk }}", self.detail)

    def test_confirmacao_deve_preservar_escopo_no_post_e_voltar(self):
        self.assertIn("escopo", self.confirm)
        self.assertIn("loja", self.confirm)
        self.assertIn("financeiro:titulo_detalhe", self.confirm)

    def test_sucesso_deve_preservar_query_de_escopo_no_redirect(self):
        block = self._cancel_block()
        self.assertIn("QueryDict", block)
        self.assertIn('"escopo"', block)
        self.assertIn('"loja"', block)