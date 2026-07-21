from pathlib import Path

from django.template.loader import get_template
from django.test import SimpleTestCase


class SidebarComprasUITest(SimpleTestCase):
    def test_sidebar_carrega(self):
        get_template('partials/sidebar.html')

    def test_sidebar_possui_links_de_compras(self):
        conteudo = Path(
            'templates/partials/sidebar.html'
        ).read_text(encoding='utf-8')

        self.assertIn(
            "compras:listar_fornecedores",
            conteudo,
        )
        self.assertIn(
            "compras:listar_pedidos_compra",
            conteudo,
        )
        self.assertIn(
            'data-menu-compras-fornecedores="true"',
            conteudo,
        )
        self.assertIn(
            'data-menu-compras-pedidos="true"',
            conteudo,
        )


class DetalhePedidoCompraUITest(SimpleTestCase):
    def test_template_detalhe_carrega(self):
        get_template(
            'compras/pedidos/detalhe.html'
        )

    def test_detalhe_possui_secoes_principais(self):
        conteudo = Path(
            'compras/templates/compras/pedidos/'
            'detalhe.html'
        ).read_text(encoding='utf-8')

        self.assertIn(
            'data-ui-pedido-itens="true"',
            conteudo,
        )
        self.assertIn(
            'data-ui-adicionar-item="true"',
            conteudo,
        )
        self.assertIn(
            'data-ui-recebimentos="true"',
            conteudo,
        )

    def test_acoes_existentes_foram_preservadas(self):
        conteudo = Path(
            'compras/templates/compras/pedidos/'
            'detalhe.html'
        ).read_text(encoding='utf-8')

        rotas = [
            'compras:editar_pedido_compra',
            'compras:adicionar_item_pedido_compra',
            'compras:remover_item_pedido_compra',
            'compras:enviar_pedido_compra',
            'compras:receber_pedido_compra',
            'compras:cancelar_pedido_compra',
            'compras:devolver_recebimento_compra',
        ]

        for rota in rotas:
            with self.subTest(rota=rota):
                self.assertIn(rota, conteudo)
