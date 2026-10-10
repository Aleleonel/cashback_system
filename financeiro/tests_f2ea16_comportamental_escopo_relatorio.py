from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import PermissaoUsuario, Usuario
from accounts.permissions import PERMISSAO_FINANCEIRO_VISUALIZAR
from empresas.models import Loja, Matriz
from financeiro.models import TituloFinanceiro
from financeiro.selectors import ESCOPO_LOJA
from financeiro.services import criar_titulo_financeiro


class F2EA16EscopoRelatorioFinanceiroBehaviorTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome="Matriz F2EA16",
            cnpj="33333333000191",
        )
        self.loja_a = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Operacional A F2EA16",
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome="Loja Operacional B F2EA16",
        )
        self.operador = Usuario.objects.create_user(
            username="operador_f2ea16",
            password="teste123",
            matriz=self.matriz,
            perfil=Usuario.PERFIL_OPERADOR,
            ativo=True,
        )
        self.operador.lojas.add(self.loja_a, self.loja_b)
        PermissaoUsuario.objects.create(
            usuario=self.operador,
            permissao=PERMISSAO_FINANCEIRO_VISUALIZAR,
        )
        self.titulo_a = self._titulo(
            loja=self.loja_a,
            chave="f2ea16-loja-a",
            descricao="Titulo exclusivo Loja A F2EA16",
            valor="111.00",
        )
        self.titulo_b = self._titulo(
            loja=self.loja_b,
            chave="f2ea16-loja-b",
            descricao="Titulo exclusivo Loja B F2EA16",
            valor="222.00",
        )

    def _titulo(self, *, loja, chave, descricao, valor):
        return criar_titulo_financeiro(
            matriz=self.matriz,
            loja=loja,
            natureza=TituloFinanceiro.Natureza.PAGAR,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave,
            chave_idempotencia=chave,
            descricao=descricao,
            data_emissao=date(2026, 10, 9),
            parcelas=[
                {
                    "numero": 1,
                    "vencimento": date(2026, 10, 31),
                    "valor": Decimal(valor),
                }
            ],
            usuario=None,
        )

    def _login_com_loja_operacional(self, loja):
        self.client.force_login(self.operador)
        session = self.client.session
        session["loja_operacional_id"] = loja.pk
        session.save()

    def test_operador_duas_lojas_usa_loja_da_sessao_e_ignora_tamper_querystring(self):
        self._login_com_loja_operacional(self.loja_b)

        response = self.client.get(
            reverse("financeiro:painel"),
            {"escopo": "loja", "loja": self.loja_a.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["escopo"], ESCOPO_LOJA)
        self.assertEqual(response.context["loja"].pk, self.loja_b.pk)
        self.assertTrue(response.context["usuario_operacional"])
        self.assertFalse(response.context["pode_filtrar_loja"])
        self.assertContains(response, "Titulo exclusivo Loja B F2EA16")
        self.assertNotContains(response, "Titulo exclusivo Loja A F2EA16")
        self.assertEqual(self.client.session["loja_operacional_id"], self.loja_b.pk)

    def test_operador_nao_expoe_outra_loja_autorizada_no_painel(self):
        self._login_com_loja_operacional(self.loja_b)

        response = self.client.get(reverse("financeiro:painel"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Loja Operacional B F2EA16")
        self.assertNotContains(response, "Loja Operacional A F2EA16")
        self.assertContains(response, "disabled")

    def test_operador_sem_sessao_define_fallback_autorizado_e_persiste(self):
        self.client.force_login(self.operador)

        response = self.client.get(reverse("financeiro:painel"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["escopo"], ESCOPO_LOJA)
        loja = response.context["loja"]
        self.assertIn(loja.pk, {self.loja_a.pk, self.loja_b.pk})
        self.assertEqual(self.client.session["loja_operacional_id"], loja.pk)

    def test_operador_sessao_invalida_nao_escapa_das_lojas_autorizadas(self):
        self.client.force_login(self.operador)
        outra_matriz = Matriz.objects.create(
            nome="Outra Matriz F2EA16",
            cnpj="44444444000191",
        )
        loja_estranha = Loja.objects.create(
            matriz=outra_matriz,
            nome="Loja Estranha F2EA16",
        )
        session = self.client.session
        session["loja_operacional_id"] = loja_estranha.pk
        session.save()

        response = self.client.get(reverse("financeiro:painel"))

        self.assertEqual(response.status_code, 200)
        loja = response.context["loja"]
        self.assertIn(loja.pk, {self.loja_a.pk, self.loja_b.pk})
        self.assertNotEqual(loja.pk, loja_estranha.pk)
        self.assertEqual(self.client.session["loja_operacional_id"], loja.pk)