from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaResgateTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(__file__).resolve().parents[2]
        cls.template = (raiz / "pdv/templates/pdv/inicio.html").read_text(encoding="utf-8")
        cls.javascript = (raiz / "pdv/static/pdv/js/frente_caixa.js").read_text(encoding="utf-8")

    def test_script_resgate_legado_nao_e_carregado(self):
        self.assertNotIn("cancelar_venda_resgate.js", self.template)

    def test_modal_profissional_existe(self):
        self.assertIn('id="pdv-modal-cancelar-venda"', self.template)
        self.assertIn('id="pdv-confirmar-cancelamento-venda"', self.template)

    def test_cancelamento_principal_nao_usa_confirm_nativo(self):
        self.assertIn('document.getElementById("pdv-cancelar-venda")', self.javascript)
        self.assertIn("window.bootstrap.Modal.getOrCreateInstance(modalEl).show()", self.javascript)
        self.assertNotIn('window.confirm("Cancelar toda a venda?', self.javascript)

    def test_confirmacao_delega_para_cancelar_venda(self):
        self.assertIn('document.getElementById("pdv-confirmar-cancelamento-venda")', self.javascript)
        self.assertIn("await cancelarVenda();", self.javascript)

    def test_backend_cancelamento_permanece_referenciado(self):
        self.assertIn("app.dataset.cancelarVendaUrl", self.javascript)