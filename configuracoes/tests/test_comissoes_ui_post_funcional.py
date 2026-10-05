from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from configuracoes.models import ConfiguracaoComissaoMatriz, MetaComissaoLoja
from configuracoes.views import comissoes
from empresas.models import Matriz, Loja

class ComissoesUIPostFuncionalTests(TestCase):
    def setUp(self):
        self.rf=RequestFactory()
        self.m1=Matriz.objects.create(nome="Matriz A")
        self.m2=Matriz.objects.create(nome="Matriz B")
        self.l1=Loja.objects.create(nome="Loja A",matriz=self.m1)
        self.l2=Loja.objects.create(nome="Loja B",matriz=self.m2)
        self.user=get_user_model().objects.create_user(username="f2d48_user",password="x",perfil="admin_loja",matriz=self.m1,ativo=True)

    def req(self,data):
        r=self.rf.post("/configuracoes/comissoes/",data)
        r.contexto_configuracoes={"escopo":"empresa","matriz":self.m1}
        r.user=self.user
        SessionMiddleware(lambda x:None).process_request(r);r.session.save()
        setattr(r,"_messages",FallbackStorage(r))
        return r

    def test_salva_politica_da_matriz_do_contexto(self):
        r=self.req({"acao":"salvar_configuracao","exigir_minimo_individual":"on","minimo_vendas_vendedor":"10000.00"})
        resp=comissoes(r)
        self.assertEqual(resp.status_code,302)
        c=ConfiguracaoComissaoMatriz.objects.get(matriz=self.m1)
        self.assertTrue(c.exigir_minimo_individual)
        self.assertEqual(c.minimo_vendas_vendedor,Decimal("10000.00"))

    def test_adiciona_meta_na_loja_do_contexto(self):
        r=self.req({"acao":"adicionar_meta","loja_id":str(self.l1.pk),"valor_meta":"50000.00","percentual_comissao":"1.50","ativa":"on"})
        resp=comissoes(r)
        self.assertEqual(resp.status_code,302)
        m=MetaComissaoLoja.objects.get(loja=self.l1)
        self.assertEqual(m.valor_meta,Decimal("50000.00"))
        self.assertEqual(m.percentual_comissao,Decimal("1.50"))

    def test_rejeita_loja_de_outra_matriz(self):
        r=self.req({"acao":"adicionar_meta","loja_id":str(self.l2.pk),"valor_meta":"70000.00","percentual_comissao":"3.00","ativa":"on"})
        resp=comissoes(r)
        self.assertEqual(resp.status_code,200)
        self.assertFalse(MetaComissaoLoja.objects.filter(loja=self.l2).exists())