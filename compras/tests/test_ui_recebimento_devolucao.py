from pathlib import Path

from django.template.loader import get_template
from django.test import SimpleTestCase


class RecebimentoCompraUITest(SimpleTestCase):
    def test_template_recebimento_carrega(self):
        get_template(
            'compras/pedidos/receber.html'
        )

    def test_recebimento_possui_estrutura_principal(self):
        conteudo = Path(
            'compras/templates/compras/pedidos/'
            'receber.html'
        ).read_text(encoding='utf-8')

        marcadores = [
            'data-ui-recebimento="true"',
            'data-ui-itens-recebimento="true"',
            'data-ui-destino-recebimento="true"',
            'Confirmar recebimento',
            'compras:detalhar_pedido_compra',
        ]

        for marcador in marcadores:
            with self.subTest(marcador=marcador):
                self.assertIn(marcador, conteudo)


class DevolucaoCompraUITest(SimpleTestCase):
    def test_template_devolucao_carrega(self):
        get_template(
            'compras/pedidos/devolver.html'
        )

    def test_devolucao_possui_estrutura_principal(self):
        conteudo = Path(
            'compras/templates/compras/pedidos/'
            'devolver.html'
        ).read_text(encoding='utf-8')

        marcadores = [
            'data-ui-devolucao="true"',
            'data-ui-itens-devolucao="true"',
            'Registrar devolução',
            'compras:detalhar_pedido_compra',
        ]

        for marcador in marcadores:
            with self.subTest(marcador=marcador):
                self.assertIn(marcador, conteudo)

    def test_templates_nao_possuem_caracteres_corrompidos(self):
        arquivos = [
            Path(
                'compras/templates/compras/pedidos/'
                'receber.html'
            ),
            Path(
                'compras/templates/compras/pedidos/'
                'devolver.html'
            ),
        ]

        for arquivo in arquivos:
            with self.subTest(arquivo=str(arquivo)):
                conteudo = arquivo.read_text(
                    encoding='utf-8'
                )

                self.assertNotIn('??', conteudo)
                self.assertNotIn('�', conteudo)
