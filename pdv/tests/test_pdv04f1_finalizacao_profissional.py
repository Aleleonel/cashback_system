from pathlib import Path

from django.template.loader import get_template
from django.test import SimpleTestCase


class Pdv04F1FinalizacaoProfissionalContratoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = Path("pdv/templates/pdv")
        cls.detalhe = (cls.root / "detalhe_venda.html").read_text(encoding="utf-8")
        cls.cabecalho = (cls.root / "partials/detalhe_venda_cabecalho.html").read_text(encoding="utf-8")
        cls.timeline = (cls.root / "partials/detalhe_venda_timeline.html").read_text(encoding="utf-8")
        cls.resumo = (cls.root / "partials/detalhe_venda_resumo.html").read_text(encoding="utf-8")

    def test_templates_compilam(self):
        for template_name in (
            "pdv/detalhe_venda.html",
            "pdv/partials/detalhe_venda_cabecalho.html",
            "pdv/partials/detalhe_venda_timeline.html",
            "pdv/partials/detalhe_venda_resumo.html",
        ):
            self.assertIsNotNone(get_template(template_name))

    def test_detalhe_usa_partials_profissionais(self):
        self.assertIn("detalhe_venda_cabecalho.html", self.detalhe)
        self.assertIn("detalhe_venda_timeline.html", self.detalhe)
        self.assertIn("detalhe_venda_resumo.html", self.detalhe)

    def test_cabecalho_destaca_identificacao_status_e_total(self):
        self.assertIn("Venda #{{ venda.numero", self.cabecalho)
        self.assertIn("venda.status == 'finalizada'", self.cabecalho)
        self.assertIn("venda.status == 'cancelada'", self.cabecalho)
        self.assertIn("R$ {{ venda.total|floatformat:2 }}", self.cabecalho)
        self.assertIn("window.print()", self.cabecalho)

    def test_timeline_contem_eventos_operacionais(self):
        for texto in (
            "Venda criada",
            "Venda finalizada",
            "Venda cancelada",
            "venda.criada_em",
            "venda.finalizada_em",
            "venda.cancelada_em",
        ):
            self.assertIn(texto, self.timeline)

    def test_resumo_financeiro_e_completo(self):
        for texto in (
            "Subtotal", "Descontos", "Acréscimos",
            "Total da venda", "Total pago", "Troco",
        ):
            self.assertIn(texto, self.resumo)

    def test_detalhe_exibe_contexto_operacional(self):
        for texto in (
            "Cliente", "Responsáveis", "Caixa e sessão",
            "Itens da venda", "Pagamentos", "Integridade operacional",
        ):
            self.assertIn(texto, self.detalhe)

    def test_templates_tratam_relacionamentos_nulos(self):
        self.assertIn("{% if venda.cliente %}", self.detalhe)
        self.assertIn("{% if venda.vendedor %}", self.detalhe)
        self.assertIn("{% if venda.operador %}", self.detalhe)
        self.assertIn("{% if venda.sessao_caixa %}", self.detalhe)

    def test_impressao_a4_permanece_disponivel(self):
        self.assertIn("@media print", self.detalhe)
        self.assertIn("@page", self.detalhe)
        self.assertIn("size: A4", self.detalhe)
        self.assertIn(".no-print", self.detalhe)
