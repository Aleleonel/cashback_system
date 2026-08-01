from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaResgateCsrfTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(__file__).resolve().parents[2]

        cls.template = (
            root / "pdv" / "templates" / "pdv" / "inicio.html"
        ).read_text(encoding="utf-8-sig")

        cls.script = (
            root
            / "pdv"
            / "static"
            / "pdv"
            / "js"
            / "cancelar_venda_resgate.js"
        ).read_text(encoding="utf-8-sig")

    def test_script_carregado_uma_vez(self):
        self.assertEqual(
            self.template.count("cancelar_venda_resgate.js"),
            1,
        )

    def test_cache_busting_atualizado(self):
        self.assertIn(
            "cancelar_venda_resgate.js?v=20260727_02",
            self.template,
        )

    def test_prioriza_token_do_formulario(self):
        self.assertIn(
            'input[name="csrfmiddlewaretoken"]',
            self.script,
        )
        self.assertIn(
            "validCsrfToken(inputToken)",
            self.script,
        )

    def test_valida_comprimento_do_token(self):
        self.assertIn(
            "value.length === 32 || value.length === 64",
            self.script,
        )

    def test_envia_token_no_header_e_corpo(self):
        self.assertIn(
            '"X-CSRFToken": token',
            self.script,
        )
        self.assertIn(
            'body.set("csrfmiddlewaretoken", token)',
            self.script,
        )

    def test_nao_exibe_html_do_erro(self):
        self.assertNotIn(
            "const text = await response.text()",
            self.script,
        )
        self.assertIn(
            "message.length <= 300",
            self.script,
        )
        self.assertIn(
            "A sessao de seguranca expirou.",
            self.script,
        )

    def test_recarrega_apos_sucesso(self):
        self.assertIn(
            "window.location.reload();",
            self.script,
        )