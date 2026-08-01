from pathlib import Path
from django.template.loader import get_template
from django.test import SimpleTestCase


class Pdv04F21CupomComercialContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cupom = Path("pdv/templates/pdv/cupom_venda_80mm.html").read_text(encoding="utf-8")
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")
        cls.historico = Path("pdv/templates/pdv/historico_vendas.html").read_text(encoding="utf-8")

    def test_template_compila(self):
        self.assertIsNotNone(get_template("pdv/cupom_venda_80mm.html"))

    def test_identidade_comercial(self):
        for texto in ("CUPOM DE VENDA", "DOCUMENTO NÃO FISCAL", "CLIENTE", "ITENS DA VENDA", "PAGAMENTOS", "CÓDIGO DE VERIFICAÇÃO", "OBRIGADO PELA PREFERÊNCIA"):
            self.assertIn(texto, self.cupom)

    def test_layout_termico_profissional(self):
        self.assertIn("size:80mm auto", self.cupom)
        self.assertIn("leader-row__dots", self.cupom)
        self.assertIn("total-box", self.cupom)
        self.assertIn("break-inside:avoid", self.cupom)

    def test_segunda_via(self):
        self.assertIn("segunda_via", self.cupom)
        self.assertIn("SEGUNDA VIA", self.cupom)
        self.assertIn('request.GET.get("via") == "2"', self.views)
        self.assertIn("?auto=1&via=2", self.historico)

    def test_codigo_verificacao(self):
        self.assertIn("V{{ venda.numero", self.cupom)
        self.assertIn("{{ venda.uuid }}", self.cupom)
