from pathlib import Path

from django.test import SimpleTestCase


class F25C16ComprasUXContractTest(SimpleTestCase):
    def setUp(self):
        self.detalhe = Path(
            "compras/templates/compras/pedidos/detalhe.html"
        ).read_text(encoding="utf-8")
        self.receber = Path(
            "compras/templates/compras/pedidos/receber.html"
        ).read_text(encoding="utf-8")

    def test_detalhe_nao_usa_confirm_nativo(self):
        self.assertNotIn("confirm(", self.detalhe)

    def test_detalhe_possui_modal_profissional_generico(self):
        self.assertIn('id="modal-confirmar-acao-pedido"', self.detalhe)
        self.assertIn("modal-dialog modal-dialog-centered", self.detalhe)
        self.assertIn('id="modal-confirmar-acao-pedido-final"', self.detalhe)

    def test_acoes_sensiveis_usam_contrato_do_modal(self):
        self.assertIn('data-confirmacao-pedido="true"', self.detalhe)
        self.assertIn('data-confirmacao-titulo=', self.detalhe)
        self.assertIn('data-confirmacao-mensagem=', self.detalhe)
        self.assertIn('data-confirmacao-botao=', self.detalhe)

    def test_observacoes_recebimento_tem_bloco_visual_padronizado(self):
        self.assertIn('data-ui-observacoes-recebimento="true"', self.receber)
        self.assertIn("form.observacoes", self.receber)