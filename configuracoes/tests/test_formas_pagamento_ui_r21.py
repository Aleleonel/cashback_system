from pathlib import Path
from django.test import SimpleTestCase

class FormaPagamentoCashbackUIR21Tests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(__file__).resolve().parents[2]
        cls.forms = (raiz / "configuracoes" / "forms.py").read_text(encoding="utf-8")
        cls.services = (raiz / "configuracoes" / "services.py").read_text(encoding="utf-8")
        cls.form_template = (raiz / "configuracoes" / "templates" / "configuracoes" / "forma_pagamento_form.html").read_text(encoding="utf-8")
        cls.lista_template = (raiz / "configuracoes" / "templates" / "configuracoes" / "formas_pagamento.html").read_text(encoding="utf-8")

    def test_form_expoe_gera_cashback(self):
        self.assertIn('"gera_cashback"', self.forms)
        self.assertIn('"Gera cashback"', self.forms)
        self.assertIn("form.gera_cashback", self.form_template)

    def test_servico_permite_persistir_gera_cashback(self):
        self.assertIn('"gera_cashback"', self.services)

    def test_lista_mostra_elegibilidade_cashback(self):
        self.assertIn("forma.gera_cashback", self.lista_template)
        self.assertIn("Cashback", self.lista_template)