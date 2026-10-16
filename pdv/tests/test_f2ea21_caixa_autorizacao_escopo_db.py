from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import PermissaoUsuario
from accounts.permissions import PERMISSAO_PDV_FECHAR_CAIXA, PERMISSAO_RELATORIOS_DASHBOARD
from empresas.models import Loja, Matriz
from pdv.models import Caixa, SessaoCaixa

class F2EA21CaixaAutorizacaoEscopoDBTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User=get_user_model()
        cls.matriz_a=Matriz.objects.create(nome="Matriz F2EA21 A")
        cls.matriz_b=Matriz.objects.create(nome="Matriz F2EA21 B")
        cls.loja_a1=Loja.objects.create(matriz=cls.matriz_a,nome="Loja A1")
        cls.loja_a2=Loja.objects.create(matriz=cls.matriz_a,nome="Loja A2")
        cls.loja_b1=Loja.objects.create(matriz=cls.matriz_b,nome="Loja B1")
        def user(nome,perfil,matriz,lojas):
            u=User.objects.create_user(username=nome,password="senha",perfil=perfil,matriz=matriz,ativo=True)
            u.lojas.set(lojas); return u
        cls.admin_relatorio=user("f21_admin_rel","sem_perfil_permissoes",cls.matriz_a,[cls.loja_a1,cls.loja_a2])
        cls.admin_caixa=user("f21_admin_caixa","sem_perfil_permissoes",cls.matriz_a,[cls.loja_a1,cls.loja_a2])
        cls.operador=user("f21_operador","operador",cls.matriz_a,[cls.loja_a1,cls.loja_a2])
        cls.sem_permissao=user("f21_sem_perm","sem_perfil_permissoes",cls.matriz_a,[cls.loja_a1])
        cls.op_sessao_a2=user("f21_op_sessao_a2","admin_loja",cls.matriz_a,[cls.loja_a2])
        cls.op_sessao_b1=user("f21_op_sessao_b1","admin_loja",cls.matriz_b,[cls.loja_b1])
        PermissaoUsuario.objects.create(usuario=cls.admin_relatorio,permissao=PERMISSAO_RELATORIOS_DASHBOARD)
        PermissaoUsuario.objects.create(usuario=cls.admin_caixa,permissao=PERMISSAO_PDV_FECHAR_CAIXA)
        PermissaoUsuario.objects.create(usuario=cls.operador,permissao=PERMISSAO_RELATORIOS_DASHBOARD)
        cls.caixa_a1=Caixa.objects.create(matriz=cls.matriz_a,loja=cls.loja_a1,nome="Caixa A1",codigo="F21A1")
        cls.caixa_a2=Caixa.objects.create(matriz=cls.matriz_a,loja=cls.loja_a2,nome="Caixa A2",codigo="F21A2")
        cls.caixa_b1=Caixa.objects.create(matriz=cls.matriz_b,loja=cls.loja_b1,nome="Caixa B1",codigo="F21B1")
        cls.sessao_a1=SessaoCaixa.objects.create(caixa=cls.caixa_a1,operador_abertura=cls.admin_relatorio)
        cls.sessao_a2=SessaoCaixa.objects.create(caixa=cls.caixa_a2,operador_abertura=cls.op_sessao_a2)
        cls.sessao_b1=SessaoCaixa.objects.create(caixa=cls.caixa_b1,operador_abertura=cls.op_sessao_b1)

    def login(self,u,loja=None):
        self.client.force_login(u); s=self.client.session
        if loja is None: s.pop("loja_operacional_id",None)
        else: s["loja_operacional_id"]=loja
        s.save()
    def history(self,**params): return self.client.get(reverse("pdv:historico_fechamentos"),params)
    def demo(self,sessao,**params): return self.client.get(reverse("pdv:demonstrativo_caixa",kwargs={"sessao_id":sessao.pk}),params)
    def ids(self,r): return {x.pk for x in r.context["sessoes"]}

    def test_relatorio_admin_sem_fechar_acessa_historico(self):
        self.login(self.admin_relatorio); r=self.history(modo_relatorio="1")
        self.assertEqual(r.status_code,200); self.assertIn(self.sessao_a1.pk,self.ids(r)); self.assertIn(self.sessao_a2.pk,self.ids(r)); self.assertNotIn(self.sessao_b1.pk,self.ids(r))
    def test_relatorio_admin_sem_fechar_acessa_demonstrativo(self):
        self.login(self.admin_relatorio); self.assertEqual(self.demo(self.sessao_a1,modo_relatorio="1").status_code,200)
    def test_operacional_fechar_sem_relatorio_acessa_historico(self):
        self.login(self.admin_caixa); self.assertEqual(self.history().status_code,200)
    def test_operacional_fechar_sem_relatorio_acessa_demonstrativo(self):
        self.login(self.admin_caixa); self.assertEqual(self.demo(self.sessao_a1).status_code,200)
    def test_sem_permissao_nao_acessa_relatorio(self):
        self.login(self.sem_permissao); self.assertEqual(self.history(modo_relatorio="1").status_code,403)
    def test_relatorio_sem_fechar_nao_acessa_modo_operacional_historico(self):
        self.login(self.admin_relatorio)
        self.assertEqual(self.history().status_code, 403)

    def test_relatorio_sem_fechar_nao_acessa_modo_operacional_demonstrativo(self):
        self.login(self.admin_relatorio)
        self.assertEqual(self.demo(self.sessao_a1).status_code, 403)

    def test_fechar_sem_relatorio_nao_acessa_modo_relatorio_historico(self):
        self.login(self.admin_caixa)
        self.assertEqual(self.history(modo_relatorio="1").status_code, 403)

    def test_fechar_sem_relatorio_nao_acessa_modo_relatorio_demonstrativo(self):
        self.login(self.admin_caixa)
        self.assertEqual(self.demo(self.sessao_a1, modo_relatorio="1").status_code, 403)

    def test_operador_relatorio_loja_operacional_ignora_tamper(self):
        self.login(self.operador,self.loja_a1.pk); r=self.history(modo_relatorio="1",loja=str(self.loja_a2.pk))
        self.assertEqual(r.status_code,200); self.assertIn(self.sessao_a1.pk,self.ids(r)); self.assertNotIn(self.sessao_a2.pk,self.ids(r))
    def test_admin_relatorio_filtra_loja_propria_matriz(self):
        self.login(self.admin_relatorio); r=self.history(modo_relatorio="1",loja=str(self.loja_a2.pk))
        self.assertEqual(r.status_code,200); self.assertNotIn(self.sessao_a1.pk,self.ids(r)); self.assertIn(self.sessao_a2.pk,self.ids(r))
    def test_admin_relatorio_nao_vaza_outra_matriz(self):
        self.login(self.admin_relatorio); r=self.history(modo_relatorio="1",loja=str(self.loja_b1.pk))
        self.assertEqual(r.status_code,200); self.assertNotIn(self.sessao_b1.pk,self.ids(r))
    def test_demonstrativo_cross_matriz_404(self):
        self.login(self.admin_relatorio); self.assertEqual(self.demo(self.sessao_b1,modo_relatorio="1").status_code,404)
    def test_operador_demonstrativo_fora_loja_operacional_404(self):
        self.login(self.operador,self.loja_a1.pk); self.assertEqual(self.demo(self.sessao_a2,modo_relatorio="1").status_code,404)
