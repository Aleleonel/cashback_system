from django.test import TestCase
from django.urls import reverse
from accounts.models import Usuario
from accounts.models import PermissaoUsuario
from accounts.permissions import PERMISSAO_FINANCEIRO_GERENCIAR
from empresas.models import Matriz
from financeiro.models import PlanoConta


class PlanoContaEdicaoComportamentoR9KUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz Edicao R9KUX")
        cls.outra_matriz = Matriz.objects.create(nome="Outra Matriz Edicao R9KUX")
        cls.user = Usuario.objects.create_user(username="gestor_edicao_r9kux", password="x", matriz=cls.matriz)
        PermissaoUsuario.objects.create(usuario=cls.user, permissao=PERMISSAO_FINANCEIRO_GERENCIAR)
        cls.plano = PlanoConta.objects.create(
            matriz=cls.matriz, codigo="5.01", nome="Despesas Operacionais",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True, ativo=True,
        )
        cls.outro = PlanoConta.objects.create(
            matriz=cls.outra_matriz, codigo="9.01", nome="Outro",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            aceita_lancamento=True, ativo=True,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_listagem_exibe_acao_editar(self):
        response = self.client.get(reverse("financeiro:planos_conta"))
        self.assertContains(response, reverse("financeiro:plano_conta_editar", kwargs={"plano_uuid": self.plano.uuid}))
        self.assertContains(response, "Editar")

    def test_get_edicao_carrega_instancia_e_nao_expoe_outra_matriz(self):
        response = self.client.get(reverse("financeiro:plano_conta_editar", kwargs={"plano_uuid": self.plano.uuid}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="5.01"')
        self.assertNotContains(response, "9.01 - Outro")

    def test_post_edita_mesmo_registro_e_sintetica_nao_aceita_lancamento(self):
        pk = self.plano.pk
        response = self.client.post(
            reverse("financeiro:plano_conta_editar", kwargs={"plano_uuid": self.plano.uuid}),
            {
                "codigo": "5.01", "nome": "DESPESAS OPERACIONAIS",
                "tipo": PlanoConta.Tipo.SINTETICA, "natureza": PlanoConta.Natureza.DESPESA,
                "pai": "", "aceita_lancamento": "on", "ativo": "on",
            },
        )
        self.assertRedirects(response, reverse("financeiro:planos_conta"))
        plano = PlanoConta.objects.get(pk=pk)
        self.assertEqual(plano.tipo, PlanoConta.Tipo.SINTETICA)
        self.assertFalse(plano.aceita_lancamento)
        self.assertEqual(PlanoConta.objects.filter(pk=pk).count(), 1)

    def test_edicao_de_plano_de_outra_matriz_retorna_404(self):
        response = self.client.get(reverse("financeiro:plano_conta_editar", kwargs={"plano_uuid": self.outro.uuid}))
        self.assertEqual(response.status_code, 404)