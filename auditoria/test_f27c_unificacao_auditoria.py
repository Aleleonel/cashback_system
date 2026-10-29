from django.test import SimpleTestCase
from django.urls import resolve, reverse

from configuracoes.catalogo import GRUPOS_CONFIGURACAO


class F27CUnificacaoAuditoriaTests(SimpleTestCase):
    def test_card_aponta_rota_canonica(self):
        grupo = next(item for item in GRUPOS_CONFIGURACAO if item.codigo == "auditoria")
        self.assertTrue(grupo.disponivel)
        self.assertEqual(grupo.url_name, "auditoria:lista_auditoria")

    def test_rota_canonica_resolve(self):
        self.assertEqual(
            resolve(reverse("auditoria:lista_auditoria")).view_name,
            "auditoria:lista_auditoria",
        )

    def test_rota_legada_empresa_permanece_resolvendo(self):
        self.assertEqual(
            resolve(reverse("empresa:auditoria")).view_name,
            "empresa:auditoria",
        )