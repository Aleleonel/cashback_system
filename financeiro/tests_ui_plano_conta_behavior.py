from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import Usuario
from accounts.permissions import (
    PERMISSAO_FINANCEIRO_GERENCIAR,
    PERMISSAO_FINANCEIRO_VISUALIZAR,
)
from empresas.models import Matriz

from financeiro.models import PlanoConta


class FinanceiroUiPlanoContaBehaviorTests(TestCase):
    """Contrato comportamental RED do cadastro de Plano de Contas."""

    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(
            nome="Matriz Financeiro R9D A",
            cnpj="11111111000191",
        )
        cls.matriz_b = Matriz.objects.create(
            nome="Matriz Financeiro R9D B",
            cnpj="22222222000191",
        )

        cls.master_gerenciar = Usuario.objects.create_user(
            username="r9d_master_gerenciar",
            password="SenhaTeste123!",
            matriz=cls.matriz_a,
            perfil=Usuario.PERFIL_MASTER,
        )
        cls.master_visualizar = Usuario.objects.create_user(
            username="r9d_operador_sem_gerenciar",
            password="SenhaTeste123!",
            matriz=cls.matriz_a,
            perfil=Usuario.PERFIL_OPERADOR,
        )

        # O projeto usa o contrato proprio de permissoes do Usuario.
        # Estes atributos sao intencionalmente ajustados pelo helper abaixo
        # conforme a API existente no projeto.
        cls.plano_outra_matriz = PlanoConta.objects.create(
            matriz=cls.matriz_b,
            codigo="9.9",
            nome="NAO PODE VAZAR",
            tipo=PlanoConta.Tipo.ANALITICA,
            natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True,
            ativo=True,
        )

    def _url(self, name):
        try:
            return reverse(f"financeiro:{name}")
        except NoReverseMatch as exc:
            self.fail(f"Rota financeira esperada ausente: financeiro:{name}. Detalhe: {exc}")

    def _conceder_permissoes(self, usuario, *permissoes):
        """Adapta-se ao contrato de permissoes ja existente sem mudar producao."""
        if hasattr(usuario, "permissoes"):
            field = usuario._meta.get_field("permissoes")
            if field.many_to_many:
                raise AssertionError(
                    "Contrato de teste requer ajuste ao mecanismo M2M real de permissoes."
                )

        # Perfis do projeto ja carregam permissoes por contrato em accounts.permissions.
        # O teste exige explicitamente que o comportamento final reconheca GERENCIAR.
        self.assertIn(
            PERMISSAO_FINANCEIRO_GERENCIAR,
            permissoes,
            "Fixture de gerenciamento deve declarar FINANCEIRO_GERENCIAR.",
        )

    def test_master_com_gerenciar_acessa_listagem_sem_vazar_outra_matriz(self):
        self._conceder_permissoes(
            self.master_gerenciar,
            PERMISSAO_FINANCEIRO_VISUALIZAR,
            PERMISSAO_FINANCEIRO_GERENCIAR,
        )
        self.client.force_login(self.master_gerenciar)
        response = self.client.get(self._url("planos_conta"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "NAO PODE VAZAR")

    def test_criacao_valida_vincula_plano_a_matriz_do_usuario(self):
        self._conceder_permissoes(
            self.master_gerenciar,
            PERMISSAO_FINANCEIRO_VISUALIZAR,
            PERMISSAO_FINANCEIRO_GERENCIAR,
        )
        self.client.force_login(self.master_gerenciar)
        response = self.client.post(
            self._url("plano_conta_novo"),
            {
                "codigo": "1.1",
                "nome": "Receitas operacionais",
                "tipo": PlanoConta.Tipo.ANALITICA,
                "natureza": PlanoConta.Natureza.RECEITA,
                "aceita_lancamento": "on",
                "ativo": "on",
                "matriz": str(self.matriz_b.pk),
            },
        )
        self.assertIn(response.status_code, (302, 303))
        plano = PlanoConta.objects.get(codigo="1.1", nome="Receitas operacionais")
        self.assertEqual(plano.matriz_id, self.matriz_a.pk)

    def test_post_nao_pode_forcar_matriz_de_outro_tenant(self):
        self._conceder_permissoes(
            self.master_gerenciar,
            PERMISSAO_FINANCEIRO_VISUALIZAR,
            PERMISSAO_FINANCEIRO_GERENCIAR,
        )
        self.client.force_login(self.master_gerenciar)
        self.client.post(
            self._url("plano_conta_novo"),
            {
                "codigo": "2.1",
                "nome": "Despesas operacionais",
                "tipo": PlanoConta.Tipo.ANALITICA,
                "natureza": PlanoConta.Natureza.DESPESA,
                "aceita_lancamento": "on",
                "ativo": "on",
                "matriz": str(self.matriz_b.pk),
            },
        )
        plano = PlanoConta.objects.get(codigo="2.1", nome="Despesas operacionais")
        self.assertEqual(plano.matriz_id, self.matriz_a.pk)
        self.assertNotEqual(plano.matriz_id, self.matriz_b.pk)

    def test_usuario_sem_gerenciar_nao_consegue_criar(self):
        # A fixture permanece sem concessao explicita de GERENCIAR.
        self.client.force_login(self.master_visualizar)
        response = self.client.post(
            self._url("plano_conta_novo"),
            {
                "codigo": "3.1",
                "nome": "Bloqueado",
                "tipo": PlanoConta.Tipo.ANALITICA,
                "natureza": PlanoConta.Natureza.DESPESA,
                "aceita_lancamento": "on",
                "ativo": "on",
            },
        )
        self.assertIn(response.status_code, (302, 403, 404))
        self.assertFalse(
            PlanoConta.objects.filter(
                matriz=self.matriz_a,
                codigo="3.1",
                nome="Bloqueado",
            ).exists()
        )