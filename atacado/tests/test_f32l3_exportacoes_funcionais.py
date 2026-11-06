from io import BytesIO
from types import SimpleNamespace
from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase
from openpyxl import load_workbook

from atacado.exports import (
    exportar_orcamento_pdf, exportar_orcamento_xlsx,
    exportar_pedido_pdf, exportar_pedido_xlsx,
)


def documento(pedido=False):
    item = SimpleNamespace(
        produto="Produto Teste",
        quantidade=Decimal("2"),
        preco_unitario_original=Decimal("100.00"),
        preco_unitario_base=Decimal("90.00"),
        preco_unitario_final=Decimal("85.00"),
        percentual_desconto_atacado=Decimal("5.00"),
        percentual_desconto=Decimal("5.00"),
        desconto_atacado=Decimal("10.00"),
        ajuste_negociado=Decimal("-5.00"),
        produto_promocional=False,
        produto_promocional_snapshot=False,
        justificativa_negociacao="Acordo comercial",
        justificativa_negociacao_snapshot="Acordo comercial",
    )
    manager = Mock()
    manager.all.return_value = [item]
    rel = Mock()
    rel.related_model.__name__ = "ItemPedidoAtacado" if pedido else "ItemOrcamentoAtacado"
    rel.get_accessor_name.return_value = "itens_fake"
    obj = SimpleNamespace(
        pk=77, numero=123, cliente="Cliente Teste", vendedor="Vendedor Teste",
        valido_ate="2026-12-31", observacoes="Obs Orcamento",
        observacoes_snapshot="Obs Pedido", subtotal_produtos=Decimal("200.00"),
        desconto_atacado=Decimal("10.00"), ajustes_negociados=Decimal("-5.00"),
        frete=Decimal("20.00"), total=Decimal("205.00"),
        itens_fake=manager, _meta=SimpleNamespace(related_objects=[rel]),
    )
    return obj


class F32L3ExportacoesFuncionaisTests(SimpleTestCase):
    def test_pdf_orcamento_real(self):
        data=exportar_orcamento_pdf(documento(False))
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 500)

    def test_pdf_pedido_real(self):
        data=exportar_pedido_pdf(documento(True))
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 500)

    def _validar_xlsx(self, data, titulo, obs):
        wb=load_workbook(BytesIO(data), data_only=True)
        ws=wb.active
        self.assertEqual(titulo, ws["A1"].value)
        valores=[c.value for row in ws.iter_rows() for c in row if c.value is not None]
        for esperado in ("Cliente Teste","Vendedor Teste","Produto Teste","Frete","Total",obs):
            self.assertIn(esperado,valores)
        self.assertIn(20, valores)
        self.assertIn(205, valores)

    def test_xlsx_orcamento_abre_e_contem_dados(self):
        self._validar_xlsx(exportar_orcamento_xlsx(documento(False)),"Orcamento de Atacado","Obs Orcamento")

    def test_xlsx_pedido_abre_e_contem_dados(self):
        self._validar_xlsx(exportar_pedido_xlsx(documento(True)),"Pedido de Atacado","Obs Pedido")
