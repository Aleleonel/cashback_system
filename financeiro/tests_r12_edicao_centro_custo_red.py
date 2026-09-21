from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import Usuario
from empresas.models import Matriz
from financeiro.models import CentroCusto, TituloFinanceiro


class EdicaoCentroCustoR12Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(nome="Matriz R12 A")
        cls.matriz_b = Matriz.objects.create(nome="Matriz R12 B")
        cls.master = Usuario.objects.create_user(
            username="master_r12", password="teste-r12", matriz=cls.matriz_a,
            perfil=Usuario.PERFIL_MASTER,
        )
        cls.master_b = Usuario.objects.create_user(
            username="master_r12_b", password="teste-r12", matriz=cls.matriz_b,
            perfil=Usuario.PERFIL_MASTER,
        )
        cls.operador = Usuario.objects.create_user(
            username="operador_r12", password="teste-r12", matriz=cls.matriz_a,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.centro = CentroCusto.objects.create(
            matriz=cls.matriz_a, codigo="R12-01", nome="Centro Original", ativo=True
        )
        cls.centro_b = CentroCusto.objects.create(
            matriz=cls.matriz_b, codigo="R12-B", nome="Centro Outra Matriz", ativo=True
        )
        cls.titulo = TituloFinanceiro.objects.create(
            matriz=cls.matriz_a,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            centro_custo=cls.centro,
            entidade_nome="Fornecedor R12",
            descricao="Titulo vinculado R12",
            valor_original="10.00",
            data_emissao="2026-09-20",
            status=TituloFinanceiro.Status.ABERTO,
        )

    def edit_url(self, centro=None):
        centro = centro or self.centro
        return reverse("financeiro:centro_custo_editar", kwargs={"centro_uuid": centro.uuid})

    def test_get_edicao_carrega_instancia(self):
        self.client.force_login(self.master)
        response = self.client.get(self.edit_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance.pk, self.centro.pk)
        self.assertContains(response, "Centro Original")

    def test_post_edita_mesmo_registro_e_preserva_vinculo(self):
        self.client.force_login(self.master)
        pk_antes, uuid_antes, matriz_antes = self.centro.pk, self.centro.uuid, self.centro.matriz_id
        response = self.client.post(
            self.edit_url(),
            {"codigo": "R12-02", "nome": "Centro Editado", "ativo": "on"},
        )
        self.assertIn(response.status_code, (302, 303))
        self.centro.refresh_from_db()
        self.titulo.refresh_from_db()
        self.assertEqual(self.centro.pk, pk_antes)
        self.assertEqual(self.centro.uuid, uuid_antes)
        self.assertEqual(self.centro.matriz_id, matriz_antes)
        self.assertEqual(self.centro.codigo, "R12-02")
        self.assertEqual(self.centro.nome, "Centro Editado")
        self.assertEqual(self.titulo.centro_custo_id, pk_antes)

    def test_centro_de_outra_matriz_nao_pode_ser_editado(self):
        self.client.force_login(self.master)
        response = self.client.get(self.edit_url(self.centro_b))
        self.assertEqual(response.status_code, 404)

    def test_usuario_sem_gerenciar_nao_edita(self):
        self.client.force_login(self.operador)
        response = self.client.get(self.edit_url())
        self.assertIn(response.status_code, (302, 403, 404))

    def test_listagem_exibe_acao_editar(self):
        self.client.force_login(self.master)
        response = self.client.get(reverse("financeiro:centros_custo"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar")
        self.assertContains(response, str(self.centro.uuid))