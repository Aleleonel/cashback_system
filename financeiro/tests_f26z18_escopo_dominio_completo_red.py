from datetime import date
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from accounts.models import Usuario
from empresas.models import Matriz, Loja
from financeiro.models import PlanoConta, TituloFinanceiro, ParcelaFinanceira
from financeiro.services import atualizar_lancamento_manual, cancelar_titulo_financeiro

class F26Z18EscopoDominioCompletoRED(TestCase):
    def setUp(self):
        self.ma=Matriz.objects.create(nome="Matriz A Z18")
        self.mb=Matriz.objects.create(nome="Matriz B Z18")
        self.a1=Loja.objects.create(matriz=self.ma,nome="A1")
        self.a2=Loja.objects.create(matriz=self.ma,nome="A2")
        self.b1=Loja.objects.create(matriz=self.mb,nome="B1")
        self.pa=PlanoConta.objects.create(matriz=self.ma,codigo="ZA",nome="Desp A",natureza="DESPESA",classificacao_dre="DESPESA_OPERACIONAL",tipo=PlanoConta.Tipo.ANALITICA,aceita_lancamento=True)
        self.pb=PlanoConta.objects.create(matriz=self.mb,codigo="ZB",nome="Desp B",natureza="DESPESA",classificacao_dre="DESPESA_OPERACIONAL",tipo=PlanoConta.Tipo.ANALITICA,aceita_lancamento=True)
        self.admin=Usuario.objects.create_user(username="adminz18",password="x",perfil=Usuario.PERFIL_ADMIN_LOJA,matriz=self.ma);self.admin.lojas.add(self.a1)
        self.master=Usuario.objects.create_user(username="masterz18",password="x",perfil=Usuario.PERFIL_MASTER,matriz=self.ma)
        self.super=Usuario.objects.create_superuser(username="superz18",password="x",email="s@x.test")
    def titulo(self,matriz,loja,plano,suf):
        t=TituloFinanceiro.objects.create(matriz=matriz,loja=loja,natureza="PAGAR",origem_tipo="MANUAL",status="ABERTO",descricao="Z18",data_emissao=date(2026,11,1),data_competencia=date(2026,11,1),plano_conta=plano,valor_bruto=Decimal("100"),valor_desconto=Decimal("0"),valor_juros=Decimal("0"),valor_original=Decimal("100"),chave_idempotencia="z18-"+suf)
        ParcelaFinanceira.objects.create(titulo=t,numero=1,vencimento=date(2026,11,20),valor_original=Decimal("100"),status="ABERTO")
        return t
    def editar(self,t,u,loja,plano):
        return atualizar_lancamento_manual(titulo=t,usuario=u,request=None,loja=loja,natureza="PAGAR",plano_conta=plano,centro_custo=None,entidade_nome="",documento_referencia="",descricao="Z18",observacao="",data_emissao=date(2026,11,1),data_competencia=date(2026,11,1),valor_bruto=Decimal("100"),valor_desconto=Decimal("0"),valor_juros=Decimal("0"),parcelas=[{"numero":1,"vencimento":date(2026,11,20),"valor":Decimal("100")}])
    def test_01_admin_nao_edita_loja_nao_atribuida(self):
        t=self.titulo(self.ma,self.a2,self.pa,"01")
        with self.assertRaises(PermissionDenied): self.editar(t,self.admin,self.a2,self.pa)
    def test_02_admin_nao_cancela_loja_nao_atribuida(self):
        t=self.titulo(self.ma,self.a2,self.pa,"02")
        with self.assertRaises(PermissionDenied): cancelar_titulo_financeiro(titulo=t,usuario=self.admin, motivo="Correcao controlada de teste")
    def test_03_admin_nao_edita_titulo_matriz_sem_loja(self):
        t=self.titulo(self.ma,None,self.pa,"03")
        with self.assertRaises(PermissionDenied): self.editar(t,self.admin,None,self.pa)
    def test_04_admin_loja_atribuida_permitida(self):
        t=self.titulo(self.ma,self.a1,self.pa,"04");self.editar(t,self.admin,self.a1,self.pa)
    def test_05_master_nao_edita_outra_matriz(self):
        t=self.titulo(self.mb,self.b1,self.pb,"05")
        with self.assertRaises(PermissionDenied): self.editar(t,self.master,self.b1,self.pb)
    def test_06_master_nao_cancela_outra_matriz(self):
        t=self.titulo(self.mb,self.b1,self.pb,"06")
        with self.assertRaises(PermissionDenied): cancelar_titulo_financeiro(titulo=t,usuario=self.master, motivo="Correcao controlada de teste")
    def test_07_master_edita_loja_da_propria_matriz(self):
        t=self.titulo(self.ma,self.a2,self.pa,"07");self.editar(t,self.master,self.a2,self.pa)
    def test_08_master_edita_titulo_matriz_sem_loja(self):
        t=self.titulo(self.ma,None,self.pa,"08");self.editar(t,self.master,None,self.pa)
    def test_09_superuser_sem_matriz_edita_globalmente(self):
        t=self.titulo(self.mb,self.b1,self.pb,"09");self.editar(t,self.super,self.b1,self.pb)
    def test_10_superuser_sem_matriz_cancela_globalmente(self):
        t=self.titulo(self.mb,self.b1,self.pb,"10");cancelar_titulo_financeiro(titulo=t,usuario=self.super, motivo="Correcao controlada de teste")