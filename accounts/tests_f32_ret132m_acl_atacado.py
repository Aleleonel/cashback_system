from types import SimpleNamespace
from unittest.mock import Mock
from django.test import SimpleTestCase
from accounts.services import usuario_tem_permissao
from accounts.permissions import PERMISSOES_POR_PERFIL, get_permissoes_extras_disponiveis

CODIGOS = ("atacado.visualizar", "atacado.criar_orcamento", "atacado.gerar_pedido")

class TestAclAtacadoF32Ret132M(SimpleTestCase):
    def usuario(self, perfil, concedidas=(), ativo=True):
        extras = Mock()
        extras.filter.side_effect = lambda permissao: SimpleNamespace(exists=lambda: permissao in concedidas)
        return SimpleNamespace(is_authenticated=True, is_superuser=False, ativo=ativo, perfil=perfil, permissoes_extras=extras)

    def test_operador_sem_permissao_nao_tem_acesso_automatico(self):
        operador=self.usuario("operador")
        for codigo in CODIGOS:
            with self.subTest(codigo=codigo):
                self.assertNotIn(codigo, PERMISSOES_POR_PERFIL["operador"])
                self.assertFalse(usuario_tem_permissao(operador,codigo))

    def test_operador_recebe_somente_permissao_expressamente_concedida(self):
        operador=self.usuario("operador",("atacado.visualizar",))
        self.assertTrue(usuario_tem_permissao(operador,"atacado.visualizar"))
        self.assertFalse(usuario_tem_permissao(operador,"atacado.criar_orcamento"))
        self.assertFalse(usuario_tem_permissao(operador,"atacado.gerar_pedido"))

    def test_perfis_administrativos_mantem_permissoes(self):
        for perfil in ("master", "admin_loja"):
            for codigo in CODIGOS:
                with self.subTest(perfil=perfil,codigo=codigo):
                    self.assertTrue(usuario_tem_permissao(self.usuario(perfil),codigo))

    def test_usuario_inativo_nao_recebe_permissoes(self):
        self.assertFalse(usuario_tem_permissao(self.usuario("operador",CODIGOS,ativo=False),CODIGOS[0]))

    def test_concessoes_atacado_aparecem_na_lista_de_permissoes_extras(self):
        codigos={item["codigo"] for item in get_permissoes_extras_disponiveis()}
        self.assertTrue(set(CODIGOS).issubset(codigos))
