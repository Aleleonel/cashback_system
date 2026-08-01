from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import PermissaoUsuario
from accounts.permissions import get_permissoes_extras_disponiveis
from accounts.services import usuario_tem_permissao
from pdv.constants import PERMISSAO_PDV_ABRIR_CAIXA, PERMISSAO_PDV_FECHAR_CAIXA


class PermissoesPdvEmpresaUsuarioTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="operador_pdv_permissoes",
            password="teste123",
            perfil=User.PERFIL_OPERADOR,
            ativo=True,
        )

    def test_catalogo_exibe_abrir_e_fechar_caixa(self):
        codigos = {item["codigo"] for item in get_permissoes_extras_disponiveis()}
        self.assertIn(PERMISSAO_PDV_ABRIR_CAIXA, codigos)
        self.assertIn(PERMISSAO_PDV_FECHAR_CAIXA, codigos)

    def test_usuario_sem_permissao_nao_fecha_caixa(self):
        self.assertFalse(usuario_tem_permissao(self.usuario, PERMISSAO_PDV_FECHAR_CAIXA))

    def test_checkbox_persistido_autoriza_fechamento(self):
        PermissaoUsuario.objects.create(
            usuario=self.usuario,
            permissao=PERMISSAO_PDV_FECHAR_CAIXA,
        )
        self.assertTrue(usuario_tem_permissao(self.usuario, PERMISSAO_PDV_FECHAR_CAIXA))

    def test_abrir_caixa_nao_concede_fechar_caixa(self):
        PermissaoUsuario.objects.create(
            usuario=self.usuario,
            permissao=PERMISSAO_PDV_ABRIR_CAIXA,
        )
        self.assertFalse(usuario_tem_permissao(self.usuario, PERMISSAO_PDV_FECHAR_CAIXA))
