from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import PermissaoUsuario
from empresas.models import Matriz, Loja
from financeiro.models import ContaFinanceira, InstituicaoBancaria


class EdicaoInstituicaoBancariaR11RedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.matriz = Matriz.objects.create(nome="Matriz R11")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja R11")
        cls.gerente = User.objects.create_user(username="gerente_r11", password="x")
        cls.bloqueado = User.objects.create_user(username="bloqueado_r11", password="x")
        # Mantem o setup alinhado ao mecanismo de permissao existente no projeto.
        PermissaoUsuario.objects.create(usuario=cls.gerente, permissao="financeiro.gerenciar")
        cls.banco = InstituicaoBancaria.objects.create(codigo_bacen="341", nome="Banco R11", ativo=True)
        cls.outro = InstituicaoBancaria.objects.create(codigo_bacen="001", nome="Outro R11", ativo=True)
        cls.conta = ContaFinanceira.objects.create(
            matriz=cls.matriz, loja=cls.loja, instituicao=cls.banco,
            nome="Conta vinculada R11", tipo=ContaFinanceira.Tipo.CONTA_CORRENTE, ativo=True,
        )

    def url_editar(self):
        return reverse("financeiro:instituicao_bancaria_editar", kwargs={"instituicao_uuid": self.banco.uuid})

    def test_rota_edicao_existe_e_get_carrega_instancia(self):
        self.client.force_login(self.gerente)
        response = self.client.get(self.url_editar())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Banco R11")
        self.assertContains(response, "341")

    def test_post_edita_mesmo_registro_e_preserva_vinculo_conta(self):
        self.client.force_login(self.gerente)
        pk_antes = self.banco.pk
        response = self.client.post(self.url_editar(), {
            "codigo_bacen": "341",
            "nome": "Banco R11 Editado",
            "ativo": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.banco.refresh_from_db()
        self.conta.refresh_from_db()
        self.assertEqual(self.banco.pk, pk_antes)
        self.assertEqual(self.banco.nome, "Banco R11 Editado")
        self.assertEqual(self.conta.instituicao_id, pk_antes)

    def test_post_rejeita_bacen_duplicado(self):
        self.client.force_login(self.gerente)
        response = self.client.post(self.url_editar(), {
            "codigo_bacen": "001",
            "nome": "Banco R11",
            "ativo": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.banco.refresh_from_db()
        self.assertEqual(self.banco.codigo_bacen, "341")

    def test_usuario_sem_gerenciar_nao_edita(self):
        self.client.force_login(self.bloqueado)
        response = self.client.post(self.url_editar(), {
            "codigo_bacen": "341",
            "nome": "Alteracao indevida",
            "ativo": "on",
        })
        self.assertNotEqual(response.status_code, 302)
        self.banco.refresh_from_db()
        self.assertEqual(self.banco.nome, "Banco R11")

    def test_listagem_exibe_acao_editar(self):
        self.client.force_login(self.gerente)
        response = self.client.get(reverse("financeiro:instituicoes_bancarias"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar")