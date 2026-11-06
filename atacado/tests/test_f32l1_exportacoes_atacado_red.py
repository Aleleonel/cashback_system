from django.test import SimpleTestCase


class F32L1ContratoExportacoesAtacadoTests(SimpleTestCase):
    def test_api_pdf_orcamento_existe(self):
        from atacado.exports import exportar_orcamento_pdf
        self.assertTrue(callable(exportar_orcamento_pdf))

    def test_api_xlsx_orcamento_existe(self):
        from atacado.exports import exportar_orcamento_xlsx
        self.assertTrue(callable(exportar_orcamento_xlsx))

    def test_api_pdf_pedido_existe(self):
        from atacado.exports import exportar_pedido_pdf
        self.assertTrue(callable(exportar_pedido_pdf))

    def test_api_xlsx_pedido_existe(self):
        from atacado.exports import exportar_pedido_xlsx
        self.assertTrue(callable(exportar_pedido_xlsx))

    def test_contrato_http_pdf_e_xlsx(self):
        from atacado.exports import (
            CONTENT_TYPE_PDF,
            CONTENT_TYPE_XLSX,
        )
        self.assertEqual("application/pdf", CONTENT_TYPE_PDF)
        self.assertEqual(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            CONTENT_TYPE_XLSX,
        )
