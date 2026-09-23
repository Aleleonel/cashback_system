from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from empresas.models import Loja, Matriz
from financeiro.models import ContaFinanceira, InstituicaoBancaria


class R16EdicaoContaFinanceiraBehaviorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz R16")
        self.outra_matriz = Matriz.objects.create(nome="Outra Matriz R16")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja R16")
        self.outra_loja = Loja.objects.create(matriz=self.outra_matriz, nome="Outra Loja R16")
        self.instituicao = InstituicaoBancaria.objects.create(nome="Banco R16", codigo_bacen="916")
        self.conta = ContaFinanceira.objects.create(
            matriz=self.matriz, loja=self.loja, instituicao=self.instituicao,
            nome="Conta Original R16", tipo="CORRENTE", agencia="001",
            numero="12345", ativo=True,
        )
        self.conta_outra = ContaFinanceira.objects.create(
            matriz=self.outra_matriz, loja=self.outra_loja, instituicao=self.instituicao,
            nome="Conta Outra Matriz R16", tipo="CORRENTE", ativo=True,
        )
        self.user = Usuario.objects.create_user(
            username="master_r16", password="senha-r16", matriz=self.matriz,
            perfil=Usuario.PERFIL_MASTER,
        )
        self.client.force_login(self.user)

    def _url(self, conta=None):
        return reverse("financeiro:conta_financeira_editar", kwargs={"conta_uuid": (conta or self.conta).uuid})

    def _payload(self, **overrides):
        data = {
            "loja": str(self.loja.pk),
            "instituicao": str(self.instituicao.pk),
            "nome": "Conta Editada R16",
            "tipo": ContaFinanceira.Tipo.CONTA_CORRENTE,
            "agencia": "002",
            "numero": "98765",
            "ativo": "on",
        }
        data.update(overrides)
        return data

    def test_get_carrega_instancia_e_modo_edicao(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["conta"], self.conta)
        self.assertTrue(response.context["modo_edicao"])
        self.assertEqual(response.context["form"].instance, self.conta)

    def test_objeto_de_outra_matriz_retorna_404(self):
        response = self.client.get(self._url(self.conta_outra))
        self.assertEqual(response.status_code, 404)

    def test_form_nao_expoe_loja_de_outra_matriz(self):
        response = self.client.get(self._url())
        qs = response.context["form"].fields["loja"].queryset
        self.assertTrue(qs.filter(pk=self.loja.pk).exists())
        self.assertFalse(qs.filter(pk=self.outra_loja.pk).exists())

    def test_post_valido_atualiza_sem_trocar_matriz(self):
        response = self.client.post(self._url(), self._payload())
        self.assertRedirects(response, reverse("financeiro:contas_financeiras"))
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.nome, "Conta Editada R16")
        self.assertEqual(self.conta.agencia, "002")
        self.assertEqual(self.conta.numero, "98765")
        self.assertEqual(self.conta.matriz, self.matriz)

    def test_post_loja_de_outra_matriz_e_invalido_sem_mutacao_parcial(self):
        original = (self.conta.nome, self.conta.loja_id, self.conta.agencia, self.conta.numero)
        response = self.client.post(self._url(), self._payload(loja=str(self.outra_loja.pk)))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.conta.refresh_from_db()
        self.assertEqual((self.conta.nome, self.conta.loja_id, self.conta.agencia, self.conta.numero), original)

    def test_sem_permissao_gerenciar_nao_edita(self):
        operador = Usuario.objects.create_user(
            username="operador_r16", password="senha-r16", matriz=self.matriz,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        operador.lojas.add(self.loja)
        self.client.force_login(operador)
        original = self.conta.nome
        response = self.client.post(self._url(), self._payload(nome="NAO DEVE SALVAR"))
        self.assertNotEqual(response.status_code, 200)
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.nome, original)