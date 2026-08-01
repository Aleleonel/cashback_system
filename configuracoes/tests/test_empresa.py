from django.test import SimpleTestCase
from django.urls import resolve, reverse

from configuracoes.catalogo import GRUPOS_CONFIGURACAO


class ConfiguracoesEmpresaCatalogoTests(SimpleTestCase):
    def test_grupo_empresa_esta_disponivel(self):
        grupo = next(
            item
            for item in GRUPOS_CONFIGURACAO
            if item.codigo == "empresa"
        )

        self.assertTrue(grupo.disponivel)
        self.assertEqual(
            grupo.url_name,
            "configuracoes:empresa",
        )


class ConfiguracoesEmpresaUrlTests(SimpleTestCase):
    def test_url_empresa_resolve(self):
        url = reverse("configuracoes:empresa")
        match = resolve(url)

        self.assertEqual(
            match.view_name,
            "configuracoes:empresa",
        )

    def test_urls_reutilizadas_da_empresa_resolvem(self):
        nomes = (
            "empresa:dashboard",
            "empresa:lista_lojas",
            "empresa:lista_usuarios",
            "empresa:configurar_cashback",
            "empresa:auditoria",
        )

        for nome in nomes:
            with self.subTest(nome=nome):
                self.assertTrue(reverse(nome))
