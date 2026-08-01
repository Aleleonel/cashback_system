from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaLimpezaVisualTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(__file__).resolve().parents[2]
        cls.javascript = (
            raiz / "pdv/static/pdv/js/frente_caixa.js"
        ).read_text(encoding="utf-8")

    def test_guarda_textos_padrao_do_template(self):
        self.assertIn("const clienteNomePadrao =", self.javascript)
        self.assertIn("const clienteDocumentoPadrao =", self.javascript)
        self.assertIn("const vendedorAtualPadrao =", self.javascript)

    def test_limpa_cliente_quando_estado_vem_sem_cliente(self):
        self.assertIn(
            "clienteNome.textContent = clienteNomePadrao;",
            self.javascript,
        )
        self.assertIn(
            "clienteDocumento.textContent = clienteDocumentoPadrao;",
            self.javascript,
        )

    def test_limpa_vendedor_quando_estado_vem_sem_vendedor(self):
        self.assertIn(
            "vendedorAtual.textContent = vendedorAtualPadrao;",
            self.javascript,
        )
        self.assertIn('vendedorSelect.value = "";', self.javascript)
        self.assertIn(
            "vendedorSelect.selectedIndex = -1;",
            self.javascript,
        )

    def test_cancelamento_recarrega_estado(self):
        self.assertIn(
            "await carregarEstado();",
            self.javascript,
        )
