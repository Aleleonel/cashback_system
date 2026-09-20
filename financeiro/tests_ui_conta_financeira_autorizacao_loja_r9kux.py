from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_GERENCIAR
from empresas.models import Loja, Matriz
from financeiro.models import ContaFinanceira, InstituicaoBancaria

class ContaFinanceiraAutorizacaoLojaR9KUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.matriz = Matriz.objects.create(nome="Matriz R9KUX11", cnpj="91919191000191")
        cls.loja_autorizada = Loja.objects.create(matriz=cls.matriz, nome="Loja Autorizada R9KUX11")
        cls.loja_nao_autorizada = Loja.objects.create(matriz=cls.matriz, nome="Loja Nao Autorizada R9KUX11")
        cls.operador = Usuario.objects.create_user(
            username="r9kux11_operador", password="SenhaTeste123!",
            matriz=cls.matriz, perfil=Usuario.PERFIL_OPERADOR,
        )
        cls.operador.lojas.add(cls.loja_autorizada)
        PermissaoUsuario.objects.create(
            usuario=cls.operador,
            permissao=PERMISSAO_FINANCEIRO_GERENCIAR,
        )
        cls.master = Usuario.objects.create_user(
            username="r9kux11_master", password="SenhaTeste123!",
            matriz=cls.matriz, perfil=Usuario.PERFIL_MASTER,
        )
        cls.instituicao = InstituicaoBancaria.objects.create(nome="Banco R9KUX11")

    def url(self):
        return reverse("financeiro:conta_financeira_nova")

    def test_operador_nao_visualiza_loja_nao_autorizada_da_mesma_matriz(self):
        self.client.force_login(self.operador)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        qs = response.context["form"].fields["loja"].queryset
        self.assertIn(self.loja_autorizada, qs)
        self.assertNotIn(self.loja_nao_autorizada, qs)

    def test_operador_post_loja_nao_autorizada_da_mesma_matriz_e_rejeitado(self):
        self.client.force_login(self.operador)
        response = self.client.post(self.url(), {
            "loja": str(self.loja_nao_autorizada.pk),
            "instituicao": str(self.instituicao.pk),
            "tipo": ContaFinanceira.Tipo.CONTA_CORRENTE,
            "nome": "Conta Indevida R9KUX11",
            "agencia": "0001",
            "numero": "999",
            "ativo": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ContaFinanceira.objects.filter(nome="Conta Indevida R9KUX11").exists())
        self.assertIn("loja", response.context["form"].errors)

    def test_master_visualiza_todas_lojas_da_matriz(self):
        self.client.force_login(self.master)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        qs = response.context["form"].fields["loja"].queryset
        self.assertIn(self.loja_autorizada, qs)
        self.assertIn(self.loja_nao_autorizada, qs)