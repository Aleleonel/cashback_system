from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class VendasComissoesViewTests(TestCase):
    def setUp(self):
        self.url = reverse("configuracoes:vendas_comissoes")
        self.user = get_user_model().objects.create_superuser(
            username="admin_cfg_vendas",
            email="admin_cfg_vendas@example.com",
            password="senha-segura-123",
        )

    def test_exige_autenticacao(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_superusuario_acessa_hub(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "configuracoes/vendas_comissoes.html",
        )

    def test_hub_exibe_oito_secoes(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["secoes"]), 8)

        titulos = {
            secao["titulo"]
            for secao in response.context["secoes"]
        }

        self.assertEqual(
            titulos,
            {
                "Regras Comerciais",
                "Tabelas de Preços",
                "Promoções",
                "Atacado",
                "Cashback Comercial",
                "Voucher",
                "Brindes",
                "Comissões",
            },
        )
