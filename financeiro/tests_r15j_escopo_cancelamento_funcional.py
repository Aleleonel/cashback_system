from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_BAIXAR
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro


class R15JEscopoCancelamentoFuncionalTests(TestCase):
    def setUp(self):
        self.matriz_a = Matriz.objects.create(nome="Matriz R15J A", cnpj="15151515000191")
        self.matriz_b = Matriz.objects.create(nome="Matriz R15J B", cnpj="16161616000191")
        self.loja_a1 = Loja.objects.create(matriz=self.matriz_a, nome="Loja R15J A1")
        self.loja_a2 = Loja.objects.create(matriz=self.matriz_a, nome="Loja R15J A2")
        self.loja_b1 = Loja.objects.create(matriz=self.matriz_b, nome="Loja R15J B1")

        self.master = Usuario.objects.create_user(
            username="master_r15j", password="teste123",
            matriz=self.matriz_a, perfil=Usuario.PERFIL_MASTER,
        )
        self.admin = Usuario.objects.create_user(
            username="admin_r15j", password="teste123",
            matriz=self.matriz_a, perfil=Usuario.PERFIL_ADMIN_LOJA,
        )
        self.admin.lojas.add(self.loja_a1)
        self.operador = Usuario.objects.create_user(
            username="operador_r15j", password="teste123",
            matriz=self.matriz_a, perfil=Usuario.PERFIL_OPERADOR,
        )
        self.operador.lojas.add(self.loja_a1)
        PermissaoUsuario.objects.create(usuario=self.master, permissao=PERMISSAO_FINANCEIRO_BAIXAR)
        PermissaoUsuario.objects.create(usuario=self.admin, permissao=PERMISSAO_FINANCEIRO_BAIXAR)
        PermissaoUsuario.objects.create(usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR)

        self.titulo_matriz = self._titulo(self.matriz_a, None, "r15j-matriz", "Titulo matriz")
        self.titulo_a1 = self._titulo(self.matriz_a, self.loja_a1, "r15j-a1", "Titulo A1")
        self.titulo_a2 = self._titulo(self.matriz_a, self.loja_a2, "r15j-a2", "Titulo A2")
        self.titulo_b1 = self._titulo(self.matriz_b, self.loja_b1, "r15j-b1", "Titulo B1")

    def _titulo(self, matriz, loja, chave, descricao):
        return criar_titulo_financeiro(
            matriz=matriz, loja=loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave, chave_idempotencia=chave,
            descricao=descricao, data_emissao=date(2026, 9, 23),
            parcelas=[{"numero": 1, "vencimento": date(2026, 9, 30), "valor": Decimal("10.00")}],
            usuario=None,
        )

    def _url(self, titulo):
        return reverse("financeiro:titulo_cancelar", args=[titulo.uuid])

    def test_master_consolidado_acessa_titulo_matriz_e_titulo_loja(self):
        self.client.force_login(self.master)
        self.assertEqual(self.client.get(self._url(self.titulo_matriz), {"escopo": "consolidado"}).status_code, 200)
        self.assertEqual(self.client.get(self._url(self.titulo_a2), {"escopo": "consolidado"}).status_code, 200)

    def test_master_matriz_acessa_somente_titulo_sem_loja(self):
        self.client.force_login(self.master)
        self.assertEqual(self.client.get(self._url(self.titulo_matriz), {"escopo": "matriz"}).status_code, 200)
        self.assertEqual(self.client.get(self._url(self.titulo_a1), {"escopo": "matriz"}).status_code, 404)

    def test_master_loja_acessa_somente_loja_selecionada(self):
        self.client.force_login(self.master)
        params = {"escopo": "loja", "loja": self.loja_a2.pk}
        self.assertEqual(self.client.get(self._url(self.titulo_a2), params).status_code, 200)
        self.assertEqual(self.client.get(self._url(self.titulo_a1), params).status_code, 404)
        self.assertEqual(self.client.get(self._url(self.titulo_matriz), params).status_code, 404)

    def test_admin_e_operador_ficam_restritos_a_loja_autorizada(self):
        for usuario in (self.admin, self.operador):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(self._url(self.titulo_a1)).status_code, 200)
            self.assertEqual(self.client.get(self._url(self.titulo_a2)).status_code, 404)
            self.assertEqual(self.client.get(self._url(self.titulo_matriz)).status_code, 404)

    def test_outra_matriz_retorna_404(self):
        self.client.force_login(self.master)
        self.assertEqual(
            self.client.get(self._url(self.titulo_b1), {"escopo": "consolidado"}).status_code,
            404,
        )

    def test_post_master_matriz_cancela_e_preserva_escopo_no_redirect(self):
        self.client.force_login(self.master)
        response = self.client.post(self._url(self.titulo_matriz) + "?escopo=matriz")
        self.assertEqual(response.status_code, 302)
        self.assertIn("escopo=matriz", response["Location"])
        self.assertNotIn("loja=", response["Location"])
        self.titulo_matriz.refresh_from_db()
        self.assertEqual(self.titulo_matriz.status, TituloFinanceiro.Status.CANCELADO)

    def test_post_master_loja_cancela_e_preserva_loja_no_redirect(self):
        self.client.force_login(self.master)
        url = self._url(self.titulo_a2) + "?escopo=loja&loja=%s" % self.loja_a2.pk
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("escopo=loja", response["Location"])
        self.assertIn("loja=%s" % self.loja_a2.pk, response["Location"])
        self.titulo_a2.refresh_from_db()
        self.assertEqual(self.titulo_a2.status, TituloFinanceiro.Status.CANCELADO)

    def test_sem_permissao_baixar_nao_cancela(self):
        PermissaoUsuario.objects.filter(
            usuario=self.operador, permissao=PERMISSAO_FINANCEIRO_BAIXAR
        ).delete()
        self.client.force_login(self.operador)
        response = self.client.post(self._url(self.titulo_a1))
        self.assertIn(response.status_code, (302, 403))
        self.titulo_a1.refresh_from_db()
        self.assertNotEqual(self.titulo_a1.status, TituloFinanceiro.Status.CANCELADO)