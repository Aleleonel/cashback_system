from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from accounts.models import PermissaoUsuario
from accounts.permissions import (
    PERMISSOES_PDV,
    PERMISSOES_PDV_OPERADOR,
    PERMISSOES_PDV_SUPERVISAO,
)
from accounts.services import usuario_tem_permissao
from pdv.constants import (
    PERMISSAO_PDV_ABRIR_CAIXA,
    PERMISSAO_PDV_AUTORIZAR_DESCONTO,
    PERMISSAO_PDV_CANCELAR_VENDA,
    PERMISSAO_PDV_FECHAR_CAIXA,
    PERMISSAO_PDV_OPERAR,
    PERMISSAO_PDV_VISUALIZAR,
)


class PerfisPermissoesPdvTests(TestCase):
    def criar_usuario(self, username, perfil):
        User = get_user_model()
        return User.objects.create_user(
            username=username,
            password="teste123",
            perfil=perfil,
            ativo=True,
        )

    def test_grupos_nao_se_sobrepoem(self):
        self.assertFalse(PERMISSOES_PDV_OPERADOR & PERMISSOES_PDV_SUPERVISAO)
        self.assertEqual(
            PERMISSOES_PDV,
            PERMISSOES_PDV_OPERADOR | PERMISSOES_PDV_SUPERVISAO,
        )

    def test_operador_visualiza_opera_e_abre(self):
        User = get_user_model()
        usuario = self.criar_usuario("operador_acl", User.PERFIL_OPERADOR)
        for permissao in (
            PERMISSAO_PDV_VISUALIZAR,
            PERMISSAO_PDV_OPERAR,
            PERMISSAO_PDV_ABRIR_CAIXA,
        ):
            self.assertTrue(usuario_tem_permissao(usuario, permissao))

    def test_operador_nao_supervisiona(self):
        User = get_user_model()
        usuario = self.criar_usuario("operador_sem_supervisao", User.PERFIL_OPERADOR)
        for permissao in (
            PERMISSAO_PDV_FECHAR_CAIXA,
            PERMISSAO_PDV_CANCELAR_VENDA,
            PERMISSAO_PDV_AUTORIZAR_DESCONTO,
        ):
            self.assertFalse(usuario_tem_permissao(usuario, permissao))

    def test_admin_loja_possui_todas(self):
        User = get_user_model()
        usuario = self.criar_usuario("admin_loja_acl", User.PERFIL_ADMIN_LOJA)
        for permissao in PERMISSOES_PDV:
            self.assertTrue(usuario_tem_permissao(usuario, permissao))

    def test_permissao_extra_eleva_operador(self):
        User = get_user_model()
        usuario = self.criar_usuario("operador_elevado", User.PERFIL_OPERADOR)
        PermissaoUsuario.objects.create(
            usuario=usuario,
            permissao=PERMISSAO_PDV_FECHAR_CAIXA,
        )
        self.assertTrue(
            usuario_tem_permissao(usuario, PERMISSAO_PDV_FECHAR_CAIXA)
        )


class ContratoProtecoesPdvTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from pathlib import Path
        cls.views = Path("pdv/views.py").read_text(encoding="utf-8")

    def assert_protegida(self, funcao, permissao):
        indice_funcao = self.views.find(f"def {funcao}(")
        indice_decorador = self.views.rfind(
            f"@require_permission({permissao})",
            0,
            indice_funcao,
        )
        self.assertGreaterEqual(indice_funcao, 0)
        self.assertGreaterEqual(indice_decorador, 0)
        self.assertLess(indice_funcao - indice_decorador, 300)

    def test_abertura_exige_permissao(self):
        self.assert_protegida("abrir_caixa", "PERMISSAO_PDV_ABRIR_CAIXA")
        self.assert_protegida("confirmar_abertura_caixa", "PERMISSAO_PDV_ABRIR_CAIXA")

    def test_inicio_exige_visualizacao(self):
        self.assert_protegida("inicio", "PERMISSAO_PDV_VISUALIZAR")

    def test_cancelamento_exige_supervisao(self):
        self.assert_protegida("cancelar_venda_web", "PERMISSAO_PDV_CANCELAR_VENDA")

    def test_operacao_exige_permissao(self):
        for funcao in (
            "adicionar_item",
            "alterar_item",
            "cancelar_item",
            "finalizar_venda_web",
        ):
            self.assert_protegida(funcao, "PERMISSAO_PDV_OPERAR")

    def test_desconto_exige_autorizacao(self):
        self.assertIn("PERMISSAO_PDV_AUTORIZAR_DESCONTO", self.views)
        self.assertIn("Usuario sem permissao para autorizar desconto.", self.views)
