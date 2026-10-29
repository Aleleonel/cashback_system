from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from configuracoes.catalogo import GRUPOS_CONFIGURACAO
from empresas.models import Matriz


class F27EComprasHubRedTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.matriz = Matriz.objects.create(nome="Matriz F27E")

    def _card(self):
        return next(
            grupo for grupo in GRUPOS_CONFIGURACAO
            if grupo.codigo == "compras"
        )

    def test_card_compras_deve_estar_disponivel_no_hub(self):
        card = self._card()
        self.assertTrue(card.disponivel)
        self.assertEqual(card.url_name, "configuracoes:compras")

    def test_rota_canonica_compras_deve_existir(self):
        try:
            url = reverse("configuracoes:compras")
        except NoReverseMatch:
            self.fail("A rota configuracoes:compras ainda nao existe.")
        self.assertEqual(url, "/configuracoes/compras/")

    def test_admin_matriz_acessa_hub_compras(self):
        user = self.User.objects.create_user(
            username="f27e_admin", password="x",
            perfil="admin_loja", matriz=self.matriz, ativo=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("configuracoes:compras"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["contexto_configuracoes"]["matriz"],
            self.matriz,
        )

    def test_superuser_sem_matriz_acessa_hub_compras(self):
        user = self.User.objects.create_superuser(
            username="f27e_super", password="x"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("configuracoes:compras"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["contexto_configuracoes"]["escopo"],
            "plataforma",
        )

    def test_operador_nao_acessa_hub_compras(self):
        user = self.User.objects.create_user(
            username="f27e_operador", password="x",
            perfil="operador", matriz=self.matriz, ativo=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("configuracoes:compras"))
        self.assertEqual(response.status_code, 403)

    def test_hub_compras_expoe_fornecedores_e_pedidos_sem_burlar_dominio(self):
        user = self.User.objects.create_user(
            username="f27e_links", password="x",
            perfil="admin_loja", matriz=self.matriz, ativo=True,
        )
        self.client.force_login(user)
        response = self.client.get(reverse("configuracoes:compras"))
        self.assertContains(response, reverse("compras:listar_fornecedores"))
        self.assertContains(response, reverse("compras:listar_pedidos_compra"))
        self.assertContains(response, "Fornecedores")
        self.assertContains(response, "Pedidos")
