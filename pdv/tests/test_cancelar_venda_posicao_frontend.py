from pathlib import Path

from django.test import SimpleTestCase


class CancelarVendaPosicaoFrontendTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(__file__).resolve().parents[2]
        cls.template = (
            raiz / "pdv/templates/pdv/inicio.html"
        ).read_text(encoding="utf-8")

    def test_existe_um_unico_botao_cancelar_venda(self):
        self.assertEqual(
            self.template.count('id="pdv-cancelar-venda"'),
            1,
        )

    def test_cancelar_venda_fica_antes_do_modal(self):
        cancelar = self.template.index('id="pdv-cancelar-venda"')
        modal = self.template.index('id="pdv-modal-fechamento"')
        self.assertLess(cancelar, modal)

    def test_cancelar_venda_nao_fica_no_modal(self):
        modal = self.template[
            self.template.index('id="pdv-modal-fechamento"'):
        ]
        self.assertNotIn('id="pdv-cancelar-venda"', modal)

    def test_finalizar_venda_permanece_na_tela_principal(self):
        finalizar = self.template.index('id="pdv-finalizar"')
        modal = self.template.index('id="pdv-modal-fechamento"')
        self.assertLess(finalizar, modal)
