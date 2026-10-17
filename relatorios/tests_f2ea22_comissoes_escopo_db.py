from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from empresas.models import Matriz, Loja
from configuracoes.models import FechamentoComissao, ComissaoVendedor

class F2EA22ComissoesEscopoDBTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U=get_user_model()
        cls.m1=Matriz.objects.create(nome="Matriz F2EA22 A")
        cls.m2=Matriz.objects.create(nome="Matriz F2EA22 Externa")
        cls.a1=Loja.objects.create(matriz=cls.m1,nome="Loja A1 F2EA22",status="ativa")
        cls.a2=Loja.objects.create(matriz=cls.m1,nome="Loja A2 F2EA22",status="ativa")
        cls.x=Loja.objects.create(matriz=cls.m2,nome="Loja X Externa F2EA22",status="ativa")
        cls.admin=U.objects.create_user(username="adm_f2ea22",password="x",perfil="admin_loja",matriz=cls.m1,ativo=True)
        cls.admin.lojas.add(cls.a1)
        cls.op=U.objects.create_user(username="op_f2ea22",password="x",perfil="operador",matriz=cls.m1,ativo=True)
        cls.op.lojas.add(cls.a1,cls.a2)
        cls.v1=U.objects.create_user(username="vend_f2ea22",password="x",first_name="Nome",last_name="Atual",matriz=cls.m1,ativo=True)
        cls.vx=U.objects.create_user(username="vend_ext_f2ea22",password="x",matriz=cls.m2,ativo=True)
        cls.f1=cls._fech(cls.m1,cls.a1,9,"82000.00","70000.00","3.0000")
        cls.f2=cls._fech(cls.m1,cls.a2,10,"50000.00","50000.00","1.5000")
        cls.fx=cls._fech(cls.m2,cls.x,9,"999999.00","900000.00","9.0000")
        cls.c1=cls._com(cls.f1,cls.v1,"Vendedor Snapshot Historico","18000.00",True,"540.00")
        cls.c2=cls._com(cls.f2,cls.v1,"Vendedor Loja A2","12000.00",True,"180.00")
        cls.cx=cls._com(cls.fx,cls.vx,"Vendedor EXTERNO PROIBIDO","999999.00",True,"89999.91")
    @classmethod
    def _fech(cls,m,l,mes,total,meta,pct):
        return FechamentoComissao.objects.create(matriz=m,loja=l,competencia_ano=2026,competencia_mes=mes,total_vendas_loja=Decimal(total),valor_meta_atingida=Decimal(meta),percentual_aplicado=Decimal(pct),exigir_minimo_individual=False,minimo_individual=Decimal("0.00"))
    @classmethod
    def _com(cls,f,v,nome,total,elegivel,valor):
        return ComissaoVendedor.objects.create(fechamento=f,vendedor=v,vendedor_uuid_original=v.uuid,vendedor_nome_original=nome,total_vendas_vendedor=Decimal(total),elegivel=elegivel,valor_comissao=Decimal(valor))
    def url(self): return reverse("relatorios:relatorio_comissoes")
    def rows(self,r): return list(r.context["page_obj"].object_list)

    def test_admin_consolida_todas_lojas_da_matriz_e_nao_vaza_externa(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertEqual(r.status_code,200)
        self.assertEqual({x.pk for x in self.rows(r)},{self.c1.pk,self.c2.pk})
        self.assertNotContains(r,"Vendedor EXTERNO PROIBIDO")

    def test_admin_filtra_loja_da_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.a2.pk})
        self.assertEqual([x.pk for x in self.rows(r)],[self.c2.pk])

    def test_admin_tamper_loja_externa_nao_vaza_e_nao_muda_escopo(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.x.pk})
        self.assertEqual({x.pk for x in self.rows(r)},{self.c1.pk,self.c2.pk})
        self.assertNotContains(r,"Vendedor EXTERNO PROIBIDO")

    def test_operador_fica_na_loja_operacional_mesmo_com_tamper_loja(self):
        self.client.force_login(self.op)
        s=self.client.session;s["loja_operacional_id"]=self.a1.pk;s.save()
        r=self.client.get(self.url(),{"loja":self.a2.pk})
        self.assertEqual([x.pk for x in self.rows(r)],[self.c1.pk])
        self.assertNotContains(r,"Vendedor Loja A2")

    def test_operador_sem_loja_operacional_tem_dataset_vazio(self):
        self.client.force_login(self.op)
        r=self.client.get(self.url())
        self.assertEqual(self.rows(r),[])

    def test_identidade_historica_usa_nome_snapshot_e_nao_nome_atual(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.a1.pk})
        self.assertContains(r,"Vendedor Snapshot Historico")
        self.assertNotContains(r,"Nome Atual")

    def test_filtros_competencia_usam_snapshot(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"ano":"2026","mes":"10"})
        self.assertEqual([x.pk for x in self.rows(r)],[self.c2.pk])

    def test_post_nao_e_aceito_em_relatorio_read_only(self):
        self.client.force_login(self.admin)
        r=self.client.post(self.url(),{"loja":self.a1.pk})
        self.assertEqual(r.status_code,405)