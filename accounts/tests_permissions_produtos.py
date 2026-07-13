from django.test import SimpleTestCase

from accounts.permissions import (
    PERMISSAO_PRODUTOS_CRIAR,
    PERMISSAO_PRODUTOS_EDITAR,
    PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
    PERMISSAO_PRODUTOS_IMPORTAR,
    PERMISSAO_PRODUTOS_VISUALIZAR,
    PERMISSOES_POR_PERFIL,
    get_permissoes_extras_disponiveis,
)


class PermissoesProdutosTestCase(SimpleTestCase):
    def test_master_possui_todas_permissoes_de_produtos(self):
        permissoes = PERMISSOES_POR_PERFIL['master']

        self.assertIn(
            PERMISSAO_PRODUTOS_VISUALIZAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_CRIAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_EDITAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_IMPORTAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
            permissoes
        )

    def test_admin_loja_possui_todas_permissoes_de_produtos(self):
        permissoes = PERMISSOES_POR_PERFIL['admin_loja']

        self.assertIn(
            PERMISSAO_PRODUTOS_VISUALIZAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_CRIAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_EDITAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_IMPORTAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
            permissoes
        )

    def test_operador_pode_visualizar_e_criar_produtos(self):
        permissoes = PERMISSOES_POR_PERFIL['operador']

        self.assertIn(
            PERMISSAO_PRODUTOS_VISUALIZAR,
            permissoes
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_CRIAR,
            permissoes
        )

    def test_operador_nao_pode_editar_por_padrao(self):
        permissoes = PERMISSOES_POR_PERFIL['operador']

        self.assertNotIn(
            PERMISSAO_PRODUTOS_EDITAR,
            permissoes
        )
        self.assertNotIn(
            PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
            permissoes
        )

    def test_permissoes_administrativas_estao_nos_extras(self):
        codigos = {
            item['codigo']
            for item in get_permissoes_extras_disponiveis()
        }

        self.assertIn(
            PERMISSAO_PRODUTOS_EDITAR,
            codigos
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_IMPORTAR,
            codigos
        )
        self.assertIn(
            PERMISSAO_PRODUTOS_GERENCIAR_AUXILIARES,
            codigos
        )


class PermissaoImportacaoProdutosTestCase(SimpleTestCase):
    def test_master_pode_importar_produtos(self):
        self.assertIn(
            PERMISSAO_PRODUTOS_IMPORTAR,
            PERMISSOES_POR_PERFIL['master']
        )

    def test_admin_loja_pode_importar_produtos(self):
        self.assertIn(
            PERMISSAO_PRODUTOS_IMPORTAR,
            PERMISSOES_POR_PERFIL['admin_loja']
        )

    def test_operador_nao_pode_importar_produtos(self):
        self.assertNotIn(
            PERMISSAO_PRODUTOS_IMPORTAR,
            PERMISSOES_POR_PERFIL['operador']
        )
