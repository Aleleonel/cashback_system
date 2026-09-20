from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import Usuario
from empresas.models import Matriz
from financeiro.models import InstituicaoBancaria


class FinanceiroUiInstituicaoBancariaBehaviorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(
            nome="Matriz Financeiro R9F A",
            cnpj="55555555000191",
        )
        cls.matriz_b = Matriz.objects.create(
            nome="Matriz Financeiro R9F B",
            cnpj="66666666000191",
        )
        cls.master_a = Usuario.objects.create_user(
            username="r9f_master_a",
            password="SenhaTeste123!",
            matriz=cls.matriz_a,
            perfil=Usuario.PERFIL_MASTER,
        )
        cls.master_b = Usuario.objects.create_user(
            username="r9f_master_b",
            password="SenhaTeste123!",
            matriz=cls.matriz_b,
            perfil=Usuario.PERFIL_MASTER,
        )
        cls.operador = Usuario.objects.create_user(
            username="r9f_operador",
            password="SenhaTeste123!",
            matriz=cls.matriz_a,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.banco_global = InstituicaoBancaria.objects.create(
            codigo_bacen="001",
            nome="Banco Global R9F",
            ativo=True,
        )

    def _url(self, name):
        try:
            return reverse(f"financeiro:{name}")
        except NoReverseMatch as exc:
            self.fail(
                f"Rota financeira esperada ausente: financeiro:{name}. "
                f"Detalhe: {exc}"
            )

    def test_master_com_gerenciar_acessa_listagem_global(self):
        self.client.force_login(self.master_a)
        response = self.client.get(self._url("instituicoes_bancarias"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Banco Global R9F")

        self.client.force_login(self.master_b)
        response = self.client.get(self._url("instituicoes_bancarias"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Banco Global R9F")

    def test_master_com_gerenciar_cria_instituicao_global(self):
        self.client.force_login(self.master_a)
        response = self.client.post(
            self._url("instituicao_bancaria_nova"),
            {
                "codigo_bacen": "237",
                "nome": "Banco Criado R9F",
                "ativo": "on",
            },
        )
        self.assertIn(response.status_code, (302, 303))
        banco = InstituicaoBancaria.objects.get(codigo_bacen="237")
        self.assertEqual(banco.nome, "Banco Criado R9F")
        self.assertFalse(hasattr(banco, "matriz_id"))
        self.assertFalse(hasattr(banco, "loja_id"))

    def test_codigo_bacen_duplicado_nao_cria_segundo_registro(self):
        self.client.force_login(self.master_a)
        response = self.client.post(
            self._url("instituicao_bancaria_nova"),
            {
                "codigo_bacen": "001",
                "nome": "Duplicado R9F",
                "ativo": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            InstituicaoBancaria.objects.filter(codigo_bacen="001").count(),
            1,
        )
        self.assertFalse(
            InstituicaoBancaria.objects.filter(nome="Duplicado R9F").exists()
        )

    def test_codigo_bacen_vazio_e_permitido(self):
        self.client.force_login(self.master_a)
        response = self.client.post(
            self._url("instituicao_bancaria_nova"),
            {
                "codigo_bacen": "",
                "nome": "Instituicao sem BACEN R9F",
                "ativo": "on",
            },
        )
        self.assertIn(response.status_code, (302, 303))
        self.assertTrue(
            InstituicaoBancaria.objects.filter(
                nome="Instituicao sem BACEN R9F"
            ).exists()
        )

    def test_usuario_sem_gerenciar_nao_consegue_criar(self):
        self.client.force_login(self.operador)
        response = self.client.post(
            self._url("instituicao_bancaria_nova"),
            {
                "codigo_bacen": "999",
                "nome": "Bloqueado R9F",
                "ativo": "on",
            },
        )
        self.assertIn(response.status_code, (302, 403, 404))
        self.assertFalse(
            InstituicaoBancaria.objects.filter(nome="Bloqueado R9F").exists()
        )