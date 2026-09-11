from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from clientes.models import Cliente
from vouchers.models import UsoVoucher, Voucher

class Cliente360UsosVoucher195F416G32Tests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.matriz=Matriz.objects.create(nome="Matriz G32")
        self.loja_a=Loja.objects.create(matriz=self.matriz,nome="Loja A G32",status=StatusOperacional.ATIVA)
        self.loja_b=Loja.objects.create(matriz=self.matriz,nome="Loja B G32",status=StatusOperacional.ATIVA)
        self.cliente=Cliente.objects.create(matriz=self.matriz,loja_cadastro=self.loja_a,nome="Cliente G32")
        self.user=User.objects.create_user(username="usuario_g32",password="senha",perfil=User.PERFIL_OPERADOR,matriz=self.matriz)
        self.user.lojas.add(self.loja_a)
        self.client.force_login(self.user)
        hoje=timezone.localdate()
        self.voucher=Voucher.objects.create(matriz=self.matriz,cliente=self.cliente,codigo="G32-V",nome="Voucher G32",tipo=Voucher.Tipo.VALOR_FIXO,valor=Decimal("10.00"),status=Voucher.Status.ATIVO,data_inicio=hoje,data_fim=hoje+timedelta(days=30),limite_utilizacao=100,total_utilizado=0)

    def uso(self, *, loja=None, cliente=None, desconto="10.00", dias=0):
        u=UsoVoucher.objects.create(matriz=self.matriz,voucher=self.voucher,cliente=cliente or self.cliente,loja=loja or self.loja_b,usuario=self.user,valor_compra=Decimal("100.00"),valor_desconto=Decimal(desconto))
        if dias:
            UsoVoucher.objects.filter(pk=u.pk).update(criado_em=timezone.now()+timedelta(days=dias))
            u.refresh_from_db()
        return u

    def get(self, **params):
        q={"secao":"vouchers"};q.update(params)
        return self.client.get(reverse("clientes:extrato_cliente",args=[self.cliente.pk]),q)

    def test_expoe_usos_do_cliente_em_qualquer_loja_da_matriz(self):
        self.uso(loja=self.loja_b,desconto="13.27")
        r=self.get()
        self.assertEqual(r.status_code,200)
        self.assertIn("usos_vouchers_page",r.context)
        self.assertEqual(r.context["usos_vouchers_page"].paginator.count,1)
        self.assertContains(r,"Loja B G32")
        self.assertContains(r,"13,27")

    def test_filtra_data_local_inclusiva_por_criado_em(self):
        self.uso(dias=-3);self.uso(dias=-1)
        inicio=(timezone.localdate()-timedelta(days=2)).isoformat()
        fim=(timezone.localdate()-timedelta(days=1)).isoformat()
        r=self.get(data_inicio_usos=inicio,data_fim_usos=fim)
        self.assertEqual(r.context["usos_vouchers_page"].paginator.count,1)

    def test_pagina_usos_independente_com_20_por_pagina(self):
        for i in range(21): self.uso(desconto="1.00")
        r=self.get(page_usos="2")
        self.assertEqual(r.context["usos_vouchers_page"].paginator.per_page,20)
        self.assertEqual(r.context["usos_vouchers_page"].number,2)
        self.assertEqual(len(r.context["usos_vouchers_page"].object_list),1)

    def test_parametros_invalidos_sao_seguros(self):
        self.uso()
        r=self.get(data_inicio_usos="x",data_fim_usos="31-99-9999",page_usos="abc")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.context["usos_vouchers_page"].paginator.count,1)

    def test_template_tem_secao_separada_de_historico(self):
        self.uso()
        r=self.get()
        self.assertContains(r,'data-cliente360-vouchers-usos="lista"')
        self.assertContains(r,"Histórico de utilizações")