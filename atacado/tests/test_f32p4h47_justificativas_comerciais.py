from types import SimpleNamespace
from django.test import SimpleTestCase
from atacado.cadastro_services import justificativa_comercial_atacado
from atacado.exports import _linha_item


class JustificativaComercialAtacadoTests(SimpleTestCase):
    def test_elegivel_sem_promocao(self):
        self.assertEqual(justificativa_comercial_atacado(promocional=False, elegivel=True), "")

    def test_promocional_elegivel(self):
        self.assertIn("n\u00e3o cumulativo", justificativa_comercial_atacado(promocional=True, elegivel=True))

    def test_nao_elegivel_sem_promocao(self):
        self.assertIn("n\u00e3o eleg\u00edvel", justificativa_comercial_atacado(promocional=False, elegivel=False))

    def test_promocional_nao_elegivel_prioriza_promocao(self):
        texto = justificativa_comercial_atacado(promocional=True, elegivel=False)
        self.assertIn("promo\u00e7\u00e3o", texto)
        self.assertNotIn("n\u00e3o eleg\u00edvel", texto)

    def test_exportacao_le_justificativa_do_snapshot(self):
        item = SimpleNamespace(
            produto="Produto exemplo", quantidade=1,
            preco_unitario_original=100, preco_unitario_base=100,
            preco_unitario_final=100, percentual_desconto_atacado=0,
            desconto_atacado=0, ajuste_negociado=0,
            produto_promocional=True,
            justificativa_negociacao=justificativa_comercial_atacado(promocional=True, elegivel=False),
        )
        linha = _linha_item(item, pedido=False)
        self.assertEqual(linha[8], "Sim")
        self.assertIn("promo\u00e7\u00e3o", linha[9])
