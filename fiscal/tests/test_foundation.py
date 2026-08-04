from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from accounts.models import PermissaoUsuario
from accounts.permissions import PERMISSOES_POR_PERFIL
from accounts.services import usuario_tem_permissao
from fiscal import views
from fiscal.constants import (
    PERMISSAO_FISCAL_CONFIGURAR,
    PERMISSAO_FISCAL_GERENCIAR_CADASTROS,
    PERMISSAO_FISCAL_VISUALIZAR,
    PERMISSOES_FISCAL,
)


class FiscalFoundationContractTests(SimpleTestCase):
    def test_url_inicial_resolve(self):
        self.assertEqual(resolve(reverse("fiscal:inicio")).func, views.inicio)

    def test_view_exige_permissao(self):
        source = Path("fiscal/views.py").read_text(encoding="utf-8")
        self.assertIn("@require_permission(PERMISSAO_FISCAL_VISUALIZAR)", source)

    def test_template_nao_libera_emissao(self):
        template = Path("fiscal/templates/fiscal/inicio.html").read_text(encoding="utf-8")
        self.assertIn("Fundacao fiscal ativa", template)
        self.assertIn("ainda nao esta liberada", template)

    def test_permissoes_fiscais_sao_distintas(self):
        self.assertEqual(len(PERMISSOES_FISCAL), 3)
        self.assertIn(PERMISSAO_FISCAL_VISUALIZAR, PERMISSOES_FISCAL)
        self.assertIn(PERMISSAO_FISCAL_CONFIGURAR, PERMISSOES_FISCAL)
        self.assertIn(PERMISSAO_FISCAL_GERENCIAR_CADASTROS, PERMISSOES_FISCAL)


class FiscalPermissionsTests(TestCase):
    def criar_usuario(self, username, perfil):
        User = get_user_model()
        return User.objects.create_user(
            username=username,
            password="teste123",
            perfil=perfil,
            ativo=True,
        )

    def test_master_e_admin_possuem_permissoes(self):
        User = get_user_model()
        for perfil in (User.PERFIL_MASTER, User.PERFIL_ADMIN_LOJA):
            usuario = self.criar_usuario(f"fiscal_{perfil}", perfil)
            for permissao in PERMISSOES_FISCAL:
                self.assertTrue(usuario_tem_permissao(usuario, permissao))

    def test_operador_nao_recebe_permissao_por_padrao(self):
        User = get_user_model()
        usuario = self.criar_usuario("fiscal_operador", User.PERFIL_OPERADOR)
        for permissao in PERMISSOES_FISCAL:
            self.assertFalse(usuario_tem_permissao(usuario, permissao))

    def test_permissao_extra_eleva_operador(self):
        User = get_user_model()
        usuario = self.criar_usuario("fiscal_operador_extra", User.PERFIL_OPERADOR)
        PermissaoUsuario.objects.create(
            usuario=usuario,
            permissao=PERMISSAO_FISCAL_VISUALIZAR,
        )
        self.assertTrue(
            usuario_tem_permissao(usuario, PERMISSAO_FISCAL_VISUALIZAR)
        )

    def test_perfis_administrativos_contem_fiscal(self):
        self.assertTrue(
            PERMISSOES_FISCAL.issubset(PERMISSOES_POR_PERFIL["master"])
        )
        self.assertTrue(
            PERMISSOES_FISCAL.issubset(PERMISSOES_POR_PERFIL["admin_loja"])
        )
