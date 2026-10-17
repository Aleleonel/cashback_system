from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Loja, Matriz
from configuracoes.models import FechamentoComissao

class FechamentoGlobalComissoesRedTests(TestCase):
    def setUp(self):
        self.m1=Matriz.objects.create(nome="Matriz Global A")
        self.m2=Matriz.objects.create(nome="Matriz Global B")
        self.l1=Loja.objects.create(nome="Loja A1",matriz=self.m1)
        self.l2=Loja.objects.create(nome="Loja A2",matriz=self.m1)
        self.ext=Loja.objects.create(nome="Loja B1",matriz=self.m2)
        self.user=get_user_model().objects.create_user(username="f23_global",password="x",perfil="admin_loja",matriz=self.m1,ativo=True)
        self.client.force_login(self.user)
        self.url=reverse("configuracoes:comissoes")

    def post_global(self, ano="2026", mes="9"):
        return self.client.post(self.url,{"acao":"fechamento_comissao","loja_fechamento_id":"todas","competencia_ano":ano,"competencia_mes":mes})

    @patch("configuracoes.services_comissoes.fechar_comissoes_competencia")
    def test_global_orquestra_exatamente_todas_lojas_da_matriz(self, fechar):
        r=self.post_global()
        self.assertEqual(r.status_code,302)
        pares={(c.kwargs["loja"].pk,c.kwargs["ano"],c.kwargs["mes"]) for c in fechar.call_args_list}
        self.assertEqual(pares,{(self.l1.pk,2026,9),(self.l2.pk,2026,9)})
        self.assertNotIn(self.ext.pk,{p[0] for p in pares})

    @patch("configuracoes.services_comissoes.fechar_comissoes_competencia")
    def test_global_repetido_delega_idempotencia_por_loja(self, fechar):
        self.post_global(); self.post_global()
        self.assertEqual(fechar.call_count,4)

    def test_global_competencia_invalida_nao_cria_snapshot(self):
        r=self.post_global(mes="13")
        self.assertEqual(r.status_code,200)
        self.assertFalse(FechamentoComissao.objects.exists())

    def test_individual_permanece_compativel(self):
        r=self.client.post(self.url,{"acao":"fechamento_comissao","loja_fechamento_id":str(self.l1.pk),"competencia_ano":"2026","competencia_mes":"9"})
        self.assertEqual(r.status_code,302)
        self.assertTrue(FechamentoComissao.objects.filter(loja=self.l1,competencia_ano=2026,competencia_mes=9).exists())
        self.assertFalse(FechamentoComissao.objects.filter(loja=self.l2).exists())