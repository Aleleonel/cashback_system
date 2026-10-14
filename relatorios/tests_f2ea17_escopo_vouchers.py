from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from clientes.models import Cliente
from empresas.models import Loja, Matriz, StatusOperacional
from vouchers.models import UsoVoucher, Voucher


class F2EA17EscopoVouchersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        U=get_user_model()
        cls.m=Matriz.objects.create(nome="Matriz F2EA17")
        cls.a=Loja.objects.create(matriz=cls.m,nome="Loja A F2EA17",status=StatusOperacional.ATIVA)
        cls.b=Loja.objects.create(matriz=cls.m,nome="Loja B F2EA17",status=StatusOperacional.ATIVA)
        cls.m2=Matriz.objects.create(nome="Matriz Externa F2EA17")
        cls.x=Loja.objects.create(matriz=cls.m2,nome="Loja X Externa",status=StatusOperacional.ATIVA)
        cls.admin=U.objects.create_user(username="adm_f2ea17",password="x",matriz=cls.m,perfil="admin_loja")
        cls.admin.lojas.add(cls.a)
        cls.op=U.objects.create_user(username="op_f2ea17",password="x",matriz=cls.m,perfil="operador")
        cls.op.lojas.add(cls.a)
        cls.admin_externo=U.objects.create_user(username="adm_ext_f2ea17",password="x",matriz=cls.m2,perfil="admin_loja")
        cls.admin_externo.lojas.add(cls.x)
        cls.c=Cliente.objects.create(matriz=cls.m,loja_cadastro=cls.a,nome="Cliente F2EA17",cpf="11122233344")
        cls.cx=Cliente.objects.create(matriz=cls.m2,loja_cadastro=cls.x,nome="Cliente Externo",cpf="55566677788")
        cls.v=Voucher.objects.create(matriz=cls.m,codigo="V-F2EA17",nome="Voucher F2EA17",tipo="valor_fixo",valor=Decimal("10.00"),data_inicio="2026-01-01",data_fim="2026-12-31",limite_utilizacao=10)
        cls.vx=Voucher.objects.create(matriz=cls.m2,codigo="VX-F2EA17",nome="Voucher Externo",tipo="valor_fixo",valor=Decimal("30.00"),data_inicio="2026-01-01",data_fim="2026-12-31",limite_utilizacao=10)
        UsoVoucher.objects.create(matriz=cls.m,voucher=cls.v,cliente=cls.c,loja=cls.a,usuario=cls.op,valor_compra=Decimal("100"),valor_desconto=Decimal("10"))
        UsoVoucher.objects.create(matriz=cls.m,voucher=cls.v,cliente=cls.c,loja=cls.b,usuario=cls.admin,valor_compra=Decimal("200"),valor_desconto=Decimal("20"))
        UsoVoucher.objects.create(matriz=cls.m2,voucher=cls.vx,cliente=cls.cx,loja=cls.x,usuario=cls.admin_externo,valor_compra=Decimal("900"),valor_desconto=Decimal("90"))

    def url(self): return reverse("relatorios:vouchers_utilizacoes")

    def test_admin_consolida_todas_lojas_da_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["quantidade"],2)
        self.assertEqual(r.context["valor_compras"],Decimal("300"))
        self.assertEqual(r.context["valor_descontos"],Decimal("30"))

    def test_admin_filtra_qualquer_loja_da_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.b.pk})
        self.assertEqual(r.context["quantidade"],1)
        self.assertEqual(r.context["valor_compras"],Decimal("200"))

    def test_admin_tamper_loja_externa_nao_vaza_dados(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"loja":self.x.pk})
        self.assertNotContains(r,"Cliente Externo")
        self.assertNotContains(r,"900.00")
        self.assertEqual(r.context["quantidade"],2)

    def test_operador_fica_na_loja_operacional_e_ignora_tamper(self):
        self.client.force_login(self.op)
        s=self.client.session;s["loja_operacional_id"]=self.a.pk;s.save()
        r=self.client.get(self.url(),{"loja":self.b.pk})
        self.assertEqual(r.context["quantidade"],1)
        self.assertEqual(r.context["valor_compras"],Decimal("100"))
        self.assertEqual(r.context["loja_filtro"],self.a)
        self.assertNotContains(r,"Loja B F2EA17")

    def test_voucher_de_outra_matriz_nao_pode_vazar(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"voucher":self.vx.pk})
        self.assertEqual(r.context["quantidade"],0)
        self.assertNotContains(r,"Voucher Externo")
    def test_filtros_data_inicio_e_fim(self):
        from datetime import datetime
        from django.utils import timezone
        usos=list(UsoVoucher.objects.filter(matriz=self.m).order_by("pk"))
        UsoVoucher.objects.filter(pk=usos[0].pk).update(criado_em=timezone.make_aware(datetime(2026,1,10,12,0)))
        UsoVoucher.objects.filter(pk=usos[1].pk).update(criado_em=timezone.make_aware(datetime(2026,2,10,12,0)))
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"data_inicio":"2026-02-01","data_fim":"2026-02-28"})
        self.assertEqual(r.context["quantidade"],1)
        self.assertEqual(r.context["valor_compras"],Decimal("200"))

    def test_datas_invalidas_sao_ignoradas_sem_erro(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url(),{"data_inicio":"invalida","data_fim":"2026-99-99"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["quantidade"],2)

    def test_paginacao_e_de_50(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertEqual(r.context["page_obj"].paginator.per_page,50)

    def test_dropdown_vouchers_fica_restrito_a_propria_matriz(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        ids=list(r.context["vouchers"].values_list("pk",flat=True))
        self.assertIn(self.v.pk,ids)
        self.assertNotIn(self.vx.pk,ids)

    def test_relatorio_nao_expoe_acoes_transacionais_de_voucher(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url())
        self.assertNotContains(r,"Novo Voucher")
        self.assertNotContains(r,"Editar")
        self.assertNotContains(r,"Inativar")

    def test_gerenciamento_vouchers_permanece_em_rota_separada(self):
        self.assertEqual(reverse("vouchers:lista_vouchers"),"/vouchers/")
        self.assertNotEqual(reverse("vouchers:lista_vouchers"),self.url())

    def test_superuser_sem_contexto_operacional_nao_e_tratado_como_admin_da_matriz(self):
        U=get_user_model()
        su=U.objects.create_superuser(username="super_f2ea17",password="x",email="super_f2ea17@example.com")
        self.client.force_login(su)
        r=self.client.get(self.url())
        self.assertNotEqual(r.status_code,200)

    def test_usuario_inativo_sem_permissao_efetiva_e_bloqueado(self):
        U=get_user_model()
        u=U.objects.create_user(username="inativo_f2ea17",password="x",matriz=self.m,perfil="admin_loja",ativo=False)
        u.lojas.add(self.a)
        self.client.force_login(u)
        r=self.client.get(self.url())
        self.assertEqual(r.status_code,403)

    def test_relatorio_exige_permissao_relatorios_dashboard_e_nao_vouchers_gerenciar(self):
        from pathlib import Path
        source=Path("relatorios/views.py").read_text(encoding="utf-8")
        inicio=source.index("def relatorio_utilizacao_vouchers")
        trecho=source[max(0,inicio-180):inicio+120]
        self.assertIn("@require_permission(PERMISSAO_RELATORIOS_DASHBOARD)",trecho)
        self.assertNotIn("PERMISSAO_VOUCHERS_GERENCIAR",trecho)
