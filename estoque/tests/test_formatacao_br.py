from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase


class FormatacaoBrasileiraTemplateTagsTestCase(SimpleTestCase):
    def renderizar(self, expressao, contexto):
        template = Template("{% load formatadores %}" + expressao)
        return template.render(Context(contexto))

    def test_moeda_br(self):
        resultado = self.renderizar(
            "{{ valor|moeda_br }}",
            {"valor": Decimal("3250.00")},
        )
        self.assertEqual(resultado, '3.250,00')

    def test_quantidade_inteira(self):
        resultado = self.renderizar(
            "{{ valor|quantidade_br }}",
            {"valor": Decimal("65.000")},
        )
        self.assertEqual(resultado, "65")

    def test_quantidade_fracionada(self):
        resultado = self.renderizar(
            "{{ valor|quantidade_br }}",
            {"valor": Decimal("12.500")},
        )
        self.assertEqual(resultado, "12,5")

    def test_composicao_monetaria_do_dashboard(self):
        resultado = self.renderizar(
            "R$ {{ valor|moeda_br }}",
            {"valor": Decimal("3250.00")},
        )
        self.assertEqual(resultado, "R$ 3.250,00")
