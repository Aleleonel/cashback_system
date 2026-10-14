from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from empresas.models import Loja, Matriz, StatusOperacional
from clientes.models import Cliente
from cashback.models import LancamentoCashback, UsoCashback

U=get_user_model()

class F2EA18ViewEscopoCashbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m=Matriz.objects.create(nome="Matriz F2EA18G1")
        cls.m2=Matriz.objects.create(nome="Matriz Externa F2EA18G1")
        cls.a=Loja.objects.create(matriz=cls.m,nome="Loja A F2EA18G1",status=StatusOperacional.ATIVA)
        cls.b=Loja.objects.create(matriz=cls.m,nome="Loja B F2EA18G1",status=StatusOperacional.ATIVA)
        cls.x=Loja.objects.create(matriz=cls.m2,nome="Loja X Externa F2EA18G1",status=StatusOperacional.ATIVA)
        cls.admin=U.objects.create_user(username="adm_f2ea18g1",password="x",matriz=cls.m,perfil="admin_loja")
        cls.admin.lojas.add(cls.a)
        cls.op=U.objects.create_user(username="op_f2ea18g1",password="x",matriz=cls.m,perfil="operador")
        cls.op.lojas.add(cls.a,cls.b)
        cls.c=Cliente.objects.create(matriz=cls.m,loja_cadastro=cls.a,nome="Cliente F2EA18G1",cpf="12345678901")
        cls.cx=Cliente.objects.create(matriz=cls.m2,loja_cadastro=cls.x,nome="Cliente Externo F2EA18G1",cpf="98765432109")
        hoje=timezone.localdate()
        cls.ea=LancamentoCashback.objects.create(matriz=cls.m,loja=cls.a,cliente=cls.c,valor_compra=Decimal("100"),valor_base_cashback=Decimal("100"),percentual_cashback=Decimal("10"),valor_cashback=Decimal("10"),valor_utilizado=Decimal("0"),data_liberacao=hoje,data_expiracao=hoje+timedelta(days=30))
        cls.eb=LancamentoCashback.objects.create(matriz=cls.m,loja=cls.b,cliente=cls.c,valor_compra=Decimal("200"),valor_base_cashback=Decimal("200"),percentual_cashback=Decimal("5"),valor_cashback=Decimal("10"),valor_utilizado=Decimal("0"),data_liberacao=hoje,data_expiracao=hoje+timedelta(days=30))
        cls.ex=LancamentoCashback.objects.create(matriz=cls.m2,loja=cls.x,cliente=cls.cx,valor_compra=Decimal("900"),valor_base_cashback=Decimal("900"),percentual_cashback=Decimal("10"),valor_cashback=Decimal("90"),valor_utilizado=Decimal("0"),data_liberacao=hoje,data_expiracao=hoje+timedelta(days=30))
        cls.ua=UsoCashback.objects.create(matriz=cls.m,loja=cls.a,cliente=cls.c,valor_usado=Decimal("4"))
        cls.ux=UsoCashback.objects.create(matriz=cls.m2,loja=cls.x,cliente=cls.cx,valor_usado=Decimal("50"))

    def url(self):
        return reverse("relatorios:cashback_movimentacoes")

    def test_admin_consolida_todas_lojas_da_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["quantidade"],3)
        self.assertEqual(r.context["total_gerado"],Decimal("20"))
        self.assertEqual(r.context["total_utilizado"],Decimal("4"))
        self.assertEqual(list(r.context["lojas"]),[self.a,self.b])
        self.assertNotContains(r,"Cliente Externo F2EA18G1")

    def test_admin_filtra_loja_da_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.b.pk})
        self.assertEqual(r.context["quantidade"],1)
        self.assertEqual(r.context["loja_filtro"],self.b)
        self.assertEqual(r.context["total_gerado"],Decimal("10"))
        self.assertEqual(r.context["total_utilizado"],Decimal("0"))

    def test_admin_tamper_loja_externa_nao_vaza(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.x.pk})
        self.assertEqual(r.context["quantidade"],3)
        self.assertIsNone(r.context["loja_filtro"])
        self.assertNotContains(r,"Cliente Externo F2EA18G1")

    def test_operador_fica_na_loja_operacional_e_ignora_tamper(self):
        self.client.force_login(self.op)
        s=self.client.session;s["loja_operacional_id"]=self.a.pk;s.save()
        r=self.client.get(self.url(),{"loja":self.b.pk})
        self.assertEqual(r.context["loja_filtro"],self.a)
        self.assertEqual(r.context["quantidade"],2)
        self.assertEqual(r.context["total_gerado"],Decimal("10"))
        self.assertEqual(r.context["total_utilizado"],Decimal("4"))
        self.assertNotContains(r,"Loja B F2EA18G1")

    def test_paginacao_50(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertEqual(r.context["page_obj"].paginator.per_page,50)

    def test_contexto_expoe_filtros_tipo_cliente_datas(self):
        self.client.force_login(self.admin)
        hoje=timezone.localdate().isoformat()
        r=self.client.get(self.url(),{"tipo":"ENTRADA","cliente":self.c.pk,"data_inicio":hoje,"data_fim":hoje})
        self.assertEqual(r.context["tipo_filtro"],"ENTRADA")
        self.assertEqual(r.context["cliente_filtro"],str(self.c.pk))
        self.assertEqual(r.context["data_inicio"],hoje)
        self.assertEqual(r.context["data_fim"],hoje)
        self.assertEqual(r.context["quantidade"],2)
        self.assertEqual(r.context["total_utilizado"],Decimal("0"))

    def test_clientes_do_filtro_somente_da_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertIn(self.c,list(r.context["clientes"]))
        self.assertNotIn(self.cx,list(r.context["clientes"]))
