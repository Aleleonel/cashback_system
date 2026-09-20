from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from accounts.models import Usuario
from empresas.models import Loja, Matriz
from financeiro.models import ContaFinanceira, InstituicaoBancaria


class FinanceiroUiContaFinanceiraBehaviorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz_a = Matriz.objects.create(nome="Matriz R9G A", cnpj="77777777000191")
        cls.matriz_b = Matriz.objects.create(nome="Matriz R9G B", cnpj="88888888000191")
        cls.loja_a = Loja.objects.create(matriz=cls.matriz_a, nome="Loja R9G A")
        cls.loja_b = Loja.objects.create(matriz=cls.matriz_b, nome="Loja R9G B")
        cls.master_a = Usuario.objects.create_user(
            username="r9g_master_a", password="SenhaTeste123!",
            matriz=cls.matriz_a, perfil=Usuario.PERFIL_MASTER,
        )
        cls.operador = Usuario.objects.create_user(
            username="r9g_operador", password="SenhaTeste123!",
            matriz=cls.matriz_a, perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.instituicao = InstituicaoBancaria.objects.create(
            codigo_bacen="341", nome="Instituicao R9G", ativo=True
        )
        cls.conta_a = ContaFinanceira.objects.create(
            matriz=cls.matriz_a, loja=cls.loja_a, instituicao=cls.instituicao,
            tipo=ContaFinanceira.Tipo.CONTA_CORRENTE, nome="Conta Matriz A",
            agencia="0001", numero="12345", ativo=True,
        )
        cls.conta_b = ContaFinanceira.objects.create(
            matriz=cls.matriz_b, loja=cls.loja_b, instituicao=cls.instituicao,
            tipo=ContaFinanceira.Tipo.POUPANCA, nome="Conta Matriz B",
            agencia="0002", numero="67890", ativo=True,
        )

    def _url(self, name):
        try:
            return reverse(f"financeiro:{name}")
        except NoReverseMatch as exc:
            self.fail(f"Rota financeira esperada ausente: financeiro:{name}. Detalhe: {exc}")

    def test_listagem_isola_contas_por_matriz(self):
        self.client.force_login(self.master_a)
        response = self.client.get(self._url("contas_financeiras"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conta Matriz A")
        self.assertNotContains(response, "Conta Matriz B")

    def test_criacao_deriva_matriz_do_usuario(self):
        self.client.force_login(self.master_a)
        response = self.client.post(
            self._url("conta_financeira_nova"),
            {
                "loja": str(self.loja_a.pk),
                "instituicao": str(self.instituicao.pk),
                "nome": "Conta Criada R9G",
                "tipo": ContaFinanceira.Tipo.CARTEIRA_DIGITAL,
                "agencia": "",
                "numero": "PIX-01",
                "ativo": "on",
                "matriz": str(self.matriz_b.pk),
            },
        )
        self.assertIn(response.status_code, (302, 303))
        conta = ContaFinanceira.objects.get(nome="Conta Criada R9G")
        self.assertEqual(conta.matriz_id, self.matriz_a.pk)
        self.assertEqual(conta.loja_id, self.loja_a.pk)

    def test_form_nao_expoe_loja_de_outra_matriz(self):
        self.client.force_login(self.master_a)
        response = self.client.get(self._url("conta_financeira_nova"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Loja R9G A")
        self.assertNotContains(response, "Loja R9G B")

    def test_post_loja_de_outra_matriz_e_rejeitado(self):
        self.client.force_login(self.master_a)
        response = self.client.post(
            self._url("conta_financeira_nova"),
            {
                "loja": str(self.loja_b.pk),
                "instituicao": str(self.instituicao.pk),
                "nome": "Conta Invalida Cross Tenant",
                "tipo": ContaFinanceira.Tipo.OUTRA,
                "agencia": "",
                "numero": "",
                "ativo": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ContaFinanceira.objects.filter(nome="Conta Invalida Cross Tenant").exists())

    def test_usuario_sem_gerenciar_nao_consegue_criar(self):
        self.client.force_login(self.operador)
        response = self.client.post(
            self._url("conta_financeira_nova"),
            {
                "loja": str(self.loja_a.pk),
                "instituicao": str(self.instituicao.pk),
                "nome": "Conta Bloqueada R9G",
                "tipo": ContaFinanceira.Tipo.OUTRA,
                "agencia": "",
                "numero": "",
                "ativo": "on",
            },
        )
        self.assertIn(response.status_code, (302, 403, 404))
        self.assertFalse(ContaFinanceira.objects.filter(nome="Conta Bloqueada R9G").exists())