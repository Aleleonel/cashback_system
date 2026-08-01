from pathlib import Path

from django.test import SimpleTestCase


class ConsolidacaoVendaContratoTests(SimpleTestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parents[2]

    def read(self, relative_path):
        return (self.project_root / relative_path).read_text(encoding="utf-8-sig")

    def test_cancelamento_possui_service_proprio(self):
        source = self.read("pdv/services/vendas/cancelamento.py")

        self.assertIn("def cancelar_venda(", source)
        self.assertIn("select_for_update()", source)
        self.assertIn("cancelar_item_venda(", source)
        self.assertIn("StatusOperacaoVenda.CANCELADA", source)

    def test_view_delega_cancelamento_para_service(self):
        source = self.read("pdv/views.py")

        self.assertIn("cancelar_venda(", source)
        self.assertNotIn("venda.itens.all().delete()", source)
        self.assertNotIn("venda.pagamentos.all().delete()", source)

    def test_voucher_desempacota_retorno_da_venda_atual(self):
        source = self.read("pdv/views.py")

        self.assertIn(
            "venda, _, _, _ = _obter_venda_atual(request, criar=False)",
            source,
        )

    def test_exports_publicam_cancelar_venda(self):
        vendas_init = self.read("pdv/services/vendas/__init__.py")
        services_init = self.read("pdv/services/__init__.py")

        self.assertIn("from .cancelamento import cancelar_venda", vendas_init)
        self.assertIn('"cancelar_venda",', vendas_init)
        self.assertIn("cancelar_venda,", services_init)
        self.assertIn('"cancelar_venda",', services_init)