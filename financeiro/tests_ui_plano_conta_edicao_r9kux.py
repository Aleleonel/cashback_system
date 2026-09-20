from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse


class PlanoContaEdicaoR9KUXRedTests(SimpleTestCase):
    def test_rota_edicao_plano_conta_existe(self):
        try:
            url = reverse(
                "financeiro:plano_conta_editar",
                kwargs={"plano_uuid": "11111111-1111-1111-1111-111111111111"},
            )
        except NoReverseMatch as exc:
            self.fail(f"Rota de edicao ausente: {exc}")

        self.assertEqual(
            url,
            "/financeiro/planos-conta/11111111-1111-1111-1111-111111111111/editar/",
        )