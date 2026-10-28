from types import SimpleNamespace
from unittest.mock import patch
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from accounts.permissions import PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA
from accounts.services import usuario_tem_permissao
from financeiro.services import reabrir_competencia_gerencial

class F26Z60ReaberturaAutorizacaoBehaviorTests(TestCase):
    def user(self, *, superuser=False, perfil="operador", ativo=True):
        u=SimpleNamespace(is_authenticated=True,is_superuser=superuser,perfil=perfil,ativo=ativo,pk=1)
        u.permissoes_extras=SimpleNamespace(filter=lambda **kw: SimpleNamespace(exists=lambda: False))
        return u

    def test_superuser_tem_capability(self):
        self.assertTrue(usuario_tem_permissao(self.user(superuser=True), PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA))

    def test_admin_loja_ativo_tem_capability_por_perfil(self):
        self.assertTrue(usuario_tem_permissao(self.user(perfil="admin_loja"), PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA))

    def test_operador_nao_herda_capability(self):
        self.assertFalse(usuario_tem_permissao(self.user(perfil="operador"), PERMISSAO_FINANCEIRO_REABRIR_COMPETENCIA))

    def test_service_bloqueia_operador_mesmo_se_capability_for_concedida(self):
        operador=self.user(perfil="operador")
        with patch("financeiro.services.usuario_tem_permissao", return_value=True):
            with self.assertRaises(PermissionDenied):
                reabrir_competencia_gerencial(fechamento=SimpleNamespace(pk=999),usuario=operador,motivo="teste")

    def test_service_bloqueia_sem_capability_antes_de_mutar(self):
        admin=self.user(perfil="admin_loja")
        with patch("financeiro.services.usuario_tem_permissao", return_value=False):
            with self.assertRaises(PermissionDenied):
                reabrir_competencia_gerencial(fechamento=SimpleNamespace(pk=999),usuario=admin,motivo="teste")
