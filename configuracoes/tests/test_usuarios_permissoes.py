from pathlib import Path

from django.test import SimpleTestCase
from django.urls import resolve, reverse

from configuracoes.catalogo import GRUPOS_CONFIGURACAO
from configuracoes.views import usuarios_permissoes


class UsuariosPermissoesConfiguracoesTests(SimpleTestCase):
    def test_grupo_usuarios_esta_disponivel(self):
        grupo = next(
            item for item in GRUPOS_CONFIGURACAO
            if item.codigo == "usuarios"
        )
        self.assertTrue(grupo.disponivel)
        self.assertEqual(grupo.url_name, "configuracoes:usuarios_permissoes")

    def test_rota_resolve_para_view_de_orquestracao(self):
        url = reverse("configuracoes:usuarios_permissoes")
        self.assertEqual(resolve(url).func, usuarios_permissoes)

    def test_template_reutiliza_rotas_existentes(self):
        template = (
            Path(__file__).resolve().parents[1]
            / "templates"
            / "configuracoes"
            / "usuarios_permissoes.html"
        )
        conteudo = template.read_text(encoding="utf-8")
        self.assertIn("empresa:lista_usuarios", conteudo)
        self.assertIn("empresa:criar_usuario", conteudo)
