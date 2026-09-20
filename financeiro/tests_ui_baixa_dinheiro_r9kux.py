from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse


class BaixaDinheiroUiRouteRedTests(SimpleTestCase):
    def test_rota_registrar_baixa_da_parcela_deve_existir(self):
        url = reverse(
            "financeiro:parcela_baixa_nova",
            kwargs={
                "titulo_uuid": "11111111-1111-1111-1111-111111111111",
                "parcela_id": 1,
            },
        )
        self.assertEqual(
            url,
            "/financeiro/titulos/11111111-1111-1111-1111-111111111111/parcelas/1/baixa/",
        )