from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Matriz, Loja
from configuracoes.models import MetaComissaoLoja

class ComissoesUIEdicaoMetaFuncionalTests(TestCase):
    def setUp(self):
        self.m1 = Matriz.objects.create(nome="Matriz Edit A")
        self.m2 = Matriz.objects.create(nome="Matriz Edit B")
        self.l1 = Loja.objects.create(nome="Loja Edit A", matriz=self.m1)
        self.l2 = Loja.objects.create(nome="Loja Edit B", matriz=self.m2)
        self.user = get_user_model().objects.create_user(username="f2d57_edit", password="x", perfil="admin_loja", matriz=self.m1, ativo=True)
        self.client.force_login(self.user)
        self.meta1 = MetaComissaoLoja.objects.create(loja=self.l1, valor_meta=Decimal("50000.00"), percentual_comissao=Decimal("1.5000"), ativa=True)
        self.meta2 = MetaComissaoLoja.objects.create(loja=self.l2, valor_meta=Decimal("70000.00"), percentual_comissao=Decimal("3.0000"), ativa=True)

    def test_edita_valor_percentual_e_desativa_meta_do_proprio_escopo(self):
        resposta = self.client.post(reverse("configuracoes:meta_comissao_editar", args=[self.meta1.pk]), {"valor_meta": "55000.00", "percentual_comissao": "2.5000"})
        self.assertEqual(resposta.status_code, 302)
        self.meta1.refresh_from_db()
        self.assertEqual(self.meta1.valor_meta, Decimal("55000.00"))
        self.assertEqual(self.meta1.percentual_comissao, Decimal("2.5000"))
        self.assertFalse(self.meta1.ativa)

    def test_pode_reativar_meta(self):
        self.meta1.ativa = False
        self.meta1.save()
        resposta = self.client.post(reverse("configuracoes:meta_comissao_editar", args=[self.meta1.pk]), {"valor_meta": "50000.00", "percentual_comissao": "1.5000", "ativa": "on"})
        self.assertEqual(resposta.status_code, 302)
        self.meta1.refresh_from_db()
        self.assertTrue(self.meta1.ativa)

    def test_bloqueia_edicao_de_meta_de_outra_matriz(self):
        antes = (self.meta2.valor_meta, self.meta2.percentual_comissao, self.meta2.ativa)
        resposta = self.client.post(reverse("configuracoes:meta_comissao_editar", args=[self.meta2.pk]), {"valor_meta": "1.00", "percentual_comissao": "99.0000"})
        self.assertEqual(resposta.status_code, 404)
        self.meta2.refresh_from_db()
        self.assertEqual((self.meta2.valor_meta, self.meta2.percentual_comissao, self.meta2.ativa), antes)