from django.test import SimpleTestCase
from django.urls import NoReverseMatch, reverse

from configuracoes.catalogo import listar_grupos_configuracao


class F27DProdutosEstoqueHubContractRedTests(SimpleTestCase):
    """Contrato arquitetural do card Produtos e estoque na Central."""

    def _grupo(self):
        return next(
            grupo
            for grupo in listar_grupos_configuracao(incluir_criticos=True)
            if grupo.codigo == "produtos_estoque"
        )

    def test_card_produtos_estoque_deve_estar_disponivel(self):
        grupo = self._grupo()
        self.assertTrue(grupo.disponivel)
        self.assertEqual(
            grupo.url_name,
            "configuracoes:produtos_estoque",
        )

    def test_rota_agregadora_deve_existir(self):
        try:
            url = reverse("configuracoes:produtos_estoque")
        except NoReverseMatch:
            self.fail(
                "A rota configuracoes:produtos_estoque ainda nao existe."
            )
        self.assertTrue(url.startswith("/"))

    def test_card_nao_deve_apontar_diretamente_para_operacao(self):
        grupo = self._grupo()
        self.assertNotEqual(grupo.url_name, "produtos:lista_produtos")
        self.assertNotEqual(grupo.url_name, "estoque:dashboard_estoque")