from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Usuario
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.services import criar_titulo_financeiro


class FinanceiroUiFuncionalHardeningTests(TestCase):
    def setUp(self):
        self.matriz_a = Matriz.objects.create(nome="Matriz A", cnpj="11111111000191")
        self.matriz_b = Matriz.objects.create(nome="Matriz B", cnpj="22222222000191")
        self.loja_a1 = Loja.objects.create(matriz=self.matriz_a, nome="Loja A1")
        self.loja_a2 = Loja.objects.create(matriz=self.matriz_a, nome="Loja A2")
        self.loja_b1 = Loja.objects.create(matriz=self.matriz_b, nome="Loja B1")

        self.master = Usuario.objects.create_user(
            username="master_fin",
            password="teste123",
            matriz=self.matriz_a,
            perfil=Usuario.PERFIL_MASTER,
        )
        self.admin = Usuario.objects.create_user(
            username="admin_fin",
            password="teste123",
            matriz=self.matriz_a,
            perfil=Usuario.PERFIL_ADMIN_LOJA,
        )
        self.admin.lojas.add(self.loja_a1)

        self.operador = Usuario.objects.create_user(
            username="operador_fin",
            password="teste123",
            matriz=self.matriz_a,
            perfil=Usuario.PERFIL_OPERADOR,
        )
        self.operador.lojas.add(self.loja_a1)

        self.titulo_matriz = self._titulo(
            matriz=self.matriz_a,
            loja=None,
            chave="matriz-a",
            origem="matriz-a",
            descricao="Conta propria matriz",
            valor="100.00",
        )
        self.titulo_a1 = self._titulo(
            matriz=self.matriz_a,
            loja=self.loja_a1,
            chave="loja-a1",
            origem="loja-a1",
            descricao="Conta Loja A1",
            valor="200.00",
        )
        self.titulo_a2 = self._titulo(
            matriz=self.matriz_a,
            loja=self.loja_a2,
            chave="loja-a2",
            origem="loja-a2",
            descricao="Conta Loja A2",
            valor="300.00",
        )
        self.titulo_b1 = self._titulo(
            matriz=self.matriz_b,
            loja=self.loja_b1,
            chave="loja-b1",
            origem="loja-b1",
            descricao="Conta Loja B1",
            valor="999.00",
        )

    def _titulo(self, *, matriz, loja, chave, origem, descricao, valor):
        return criar_titulo_financeiro(
            matriz=matriz,
            loja=loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=origem,
            chave_idempotencia=chave,
            descricao=descricao,

            data_emissao=date(2026, 9, 14),
            parcelas=[
                {
                    "numero": 1,
                    "vencimento": date(2026, 9, 30),
                    "valor": Decimal(valor),
                }
            ],
            usuario=None,
        )

    def test_master_consolidado_enxerga_matriz_e_todas_lojas_da_propria_matriz(self):
        self.client.force_login(self.master)
        response = self.client.get(reverse("financeiro:painel"), {"escopo": "consolidado"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Conta propria matriz", content)
        self.assertIn("Conta Loja A1", content)
        self.assertIn("Conta Loja A2", content)
        self.assertNotIn("Conta Loja B1", content)

    def test_master_somente_matriz_nao_enxerga_contas_das_lojas(self):
        self.client.force_login(self.master)
        response = self.client.get(reverse("financeiro:painel"), {"escopo": "matriz"})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Conta propria matriz", content)
        self.assertNotIn("Conta Loja A1", content)
        self.assertNotIn("Conta Loja A2", content)

    def test_master_filtro_loja_enxerga_apenas_loja_escolhida(self):
        self.client.force_login(self.master)
        response = self.client.get(
            reverse("financeiro:painel"),
            {"escopo": "loja", "loja": self.loja_a2.pk},
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Conta Loja A2", content)
        self.assertNotIn("Conta Loja A1", content)
        self.assertNotIn("Conta propria matriz", content)

    def test_master_nao_pode_filtrar_loja_de_outra_matriz(self):
        self.client.force_login(self.master)
        response = self.client.get(
            reverse("financeiro:painel"),
            {"escopo": "loja", "loja": self.loja_b1.pk},
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_loja_fica_forcado_na_loja_autorizada(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("financeiro:painel"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Conta Loja A1", content)
        self.assertNotIn("Conta Loja A2", content)
        self.assertNotIn("Conta propria matriz", content)

    def test_admin_loja_nao_pode_forcar_outra_loja_da_mesma_matriz(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("financeiro:painel"),
            {"escopo": "loja", "loja": self.loja_a2.pk},
        )
        self.assertEqual(response.status_code, 404)

    def test_operador_sem_permissao_financeira_e_bloqueado(self):
        self.client.force_login(self.operador)
        response = self.client.get(reverse("financeiro:painel"))
        self.assertIn(response.status_code, (302, 403))

    def test_detalhe_master_respeita_matriz(self):
        self.client.force_login(self.master)
        response = self.client.get(
            reverse("financeiro:titulo_detalhe", args=[self.titulo_b1.uuid]),
            {"escopo": "consolidado"},
        )
        self.assertEqual(response.status_code, 404)

    def test_detalhe_admin_respeita_loja_autorizada(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("financeiro:titulo_detalhe", args=[self.titulo_a2.uuid]),
            {"escopo": "loja", "loja": self.loja_a2.pk},
        )
        self.assertEqual(response.status_code, 404)

    def test_sidebar_master_contem_financeiro(self):
        self.client.force_login(self.master)
        response = self.client.get(reverse("financeiro:painel"), {"escopo": "consolidado"})
        self.assertContains(response, 'data-sidebar-section="financeiro"')
        self.assertContains(response, "Painel financeiro")

    def test_sidebar_operador_nao_contem_financeiro(self):
        self.client.force_login(self.operador)
        response = self.client.get("/")
        if response.status_code == 200:
            self.assertNotContains(response, 'data-sidebar-section="financeiro"')