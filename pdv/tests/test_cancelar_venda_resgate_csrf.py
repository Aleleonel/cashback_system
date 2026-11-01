from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaResgateCsrfTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(__file__).resolve().parents[2]
        cls.template = (raiz / "pdv/templates/pdv/inicio.html").read_text(encoding="utf-8")
        cls.javascript = (raiz / "pdv/static/pdv/js/frente_caixa.js").read_text(encoding="utf-8")

    def test_script_legado_nao_e_carregado(self):
        self.assertNotIn("cancelar_venda_resgate.js", self.template)

    def test_frente_caixa_carregado_uma_vez(self):
        self.assertEqual(self.template.count("frente_caixa.js"), 1)

    def test_csrf_permanece_no_fluxo_principal(self):
        self.assertIn('"X-CSRFToken": csrfToken()', self.javascript)
        self.assertIn('"X-Requested-With": "XMLHttpRequest"', self.javascript)

    def test_token_prioriza_html_e_valida_comprimento(self):
        self.assertIn('input[name="csrfmiddlewaretoken"]', self.javascript)
        self.assertIn("tokenDoHtml.length === 32 || tokenDoHtml.length === 64", self.javascript)

    def test_cancelamento_recarrega_estado_sem_reload_de_pagina(self):
        self.assertIn("await carregarEstado();", self.javascript)
        self.assertNotIn("window.location.reload()", self.javascript)