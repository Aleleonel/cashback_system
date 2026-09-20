from django.test import TestCase
from accounts.models import Usuario, PermissaoUsuario
from accounts.permissions import (
    PERMISSAO_FINANCEIRO_VISUALIZAR,
    PERMISSAO_FINANCEIRO_LANCAR_DESPESA,
    PERMISSAO_FINANCEIRO_BAIXAR,
)
from empresas.models import Matriz, Loja
from empresa.services import sincronizar_permissoes_extras_usuario_empresa


class PersistenciaPermissoesOperacionaisR9KUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz Permissoes R9KUX15K")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja Permissoes R9KUX15K")
        cls.executor = Usuario.objects.create_user(
            username="r9kux15k_admin", password="x", matriz=cls.matriz,
            perfil=Usuario.PERFIL_MASTER,
        )
        cls.operador = Usuario.objects.create_user(
            username="r9kux15k_operador", password="x", matriz=cls.matriz,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.operador.lojas.add(cls.loja)

    def test_marcar_permissoes_cria_registros(self):
        desejadas = {
            PERMISSAO_FINANCEIRO_VISUALIZAR,
            PERMISSAO_FINANCEIRO_LANCAR_DESPESA,
            PERMISSAO_FINANCEIRO_BAIXAR,
        }
        sincronizar_permissoes_extras_usuario_empresa(
            usuario=self.operador,
            permissoes=desejadas,
            usuario_executor=self.executor,
        )
        atuais = set(
            self.operador.permissoes_extras.values_list("permissao", flat=True)
        )
        self.assertEqual(atuais, desejadas)

    def test_desmarcar_remove_somente_permissao_retirada(self):
        iniciais = {
            PERMISSAO_FINANCEIRO_VISUALIZAR,
            PERMISSAO_FINANCEIRO_LANCAR_DESPESA,
            PERMISSAO_FINANCEIRO_BAIXAR,
        }
        sincronizar_permissoes_extras_usuario_empresa(
            usuario=self.operador,
            permissoes=iniciais,
            usuario_executor=self.executor,
        )
        finais = {
            PERMISSAO_FINANCEIRO_VISUALIZAR,
            PERMISSAO_FINANCEIRO_BAIXAR,
        }
        sincronizar_permissoes_extras_usuario_empresa(
            usuario=self.operador,
            permissoes=finais,
            usuario_executor=self.executor,
        )
        atuais = set(
            self.operador.permissoes_extras.values_list("permissao", flat=True)
        )
        self.assertEqual(atuais, finais)
        self.assertFalse(
            PermissaoUsuario.objects.filter(
                usuario=self.operador,
                permissao=PERMISSAO_FINANCEIRO_LANCAR_DESPESA,
            ).exists()
        )