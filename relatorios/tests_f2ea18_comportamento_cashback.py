from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.utils import timezone
from empresas.models import Matriz, Loja
from clientes.models import Cliente
from cashback.models import LancamentoCashback, UsoCashback
from cashback.selectors import get_relatorio_movimentacoes_cashback

class F2EA18SelectorComportamentoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m1=Matriz.objects.create(nome="MATRIZ F2EA18 A")
        cls.m2=Matriz.objects.create(nome="MATRIZ F2EA18 B")
        cls.l1=Loja.objects.create(matriz=cls.m1,nome="LOJA A1")
        cls.l2=Loja.objects.create(matriz=cls.m1,nome="LOJA A2")
        cls.lx=Loja.objects.create(matriz=cls.m2,nome="LOJA B1")
        cls.c1=Cliente.objects.create(matriz=cls.m1,loja_cadastro=cls.l1,nome="CLIENTE A")
        cls.cx=Cliente.objects.create(matriz=cls.m2,loja_cadastro=cls.lx,nome="CLIENTE B")
        hoje=timezone.localdate()
        cls.e1=LancamentoCashback.objects.create(matriz=cls.m1,loja=cls.l1,cliente=cls.c1,valor_compra=Decimal("100.00"),valor_base_cashback=Decimal("100.00"),percentual_cashback=Decimal("10.00"),valor_cashback=Decimal("10.00"),valor_utilizado=Decimal("0.00"),data_liberacao=hoje,data_expiracao=hoje+timedelta(days=30))
        cls.e2=LancamentoCashback.objects.create(matriz=cls.m1,loja=cls.l2,cliente=cls.c1,valor_compra=Decimal("200.00"),valor_base_cashback=Decimal("200.00"),percentual_cashback=Decimal("5.00"),valor_cashback=Decimal("10.00"),valor_utilizado=Decimal("0.00"),data_liberacao=hoje,data_expiracao=hoje+timedelta(days=30))
        cls.ex=LancamentoCashback.objects.create(matriz=cls.m2,loja=cls.lx,cliente=cls.cx,valor_compra=Decimal("999.00"),valor_base_cashback=Decimal("999.00"),percentual_cashback=Decimal("10.00"),valor_cashback=Decimal("99.90"),valor_utilizado=Decimal("0.00"),data_liberacao=hoje,data_expiracao=hoje+timedelta(days=30))
        cls.u1=UsoCashback.objects.create(matriz=cls.m1,loja=cls.l1,cliente=cls.c1,valor_usado=Decimal("4.00"))
        cls.ux=UsoCashback.objects.create(matriz=cls.m2,loja=cls.lx,cliente=cls.cx,valor_usado=Decimal("50.00"))

    def test_retorna_estrutura_administrativa_unificada(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1)
        self.assertIsInstance(r,dict)
        self.assertIn("movimentacoes",r)
        self.assertIn("quantidade_movimentacoes",r)
        self.assertIn("total_gerado",r)
        self.assertIn("total_utilizado",r)

    def test_isolamento_cross_matriz(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1)
        self.assertEqual(r["quantidade_movimentacoes"],3)
        self.assertEqual(r["total_gerado"],Decimal("20.00"))
        self.assertEqual(r["total_utilizado"],Decimal("4.00"))
        self.assertFalse(any(x.get("loja_id")==self.lx.pk for x in r["movimentacoes"]))

    def test_filtro_loja_limita_entradas_e_saidas(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1,loja=self.l1)
        self.assertEqual(r["quantidade_movimentacoes"],2)
        self.assertTrue(all(x["loja_id"]==self.l1.pk for x in r["movimentacoes"]))

    def test_filtro_tipo_entrada(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1,tipo="ENTRADA")
        self.assertEqual(r["quantidade_movimentacoes"],2)
        self.assertTrue(all(x["tipo"]=="ENTRADA" for x in r["movimentacoes"]))
        self.assertEqual(r["total_utilizado"],Decimal("0.00"))

    def test_filtro_tipo_saida(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1,tipo="SAIDA")
        self.assertEqual(r["quantidade_movimentacoes"],1)
        self.assertTrue(all(x["tipo"]=="SAIDA" for x in r["movimentacoes"]))
        self.assertEqual(r["total_gerado"],Decimal("0.00"))

    def test_linha_entrada_expoe_campos_contrato(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1,loja=self.l2)
        x=r["movimentacoes"][0]
        for k in ("data","tipo","cliente","cliente_id","loja","loja_id","valor_compra","percentual_cashback","entrada","saida"):
            self.assertIn(k,x)
        self.assertEqual(x["entrada"],Decimal("10.00"))
        self.assertEqual(x["saida"],Decimal("0.00"))

    def test_ordenacao_data_desc(self):
        r=get_relatorio_movimentacoes_cashback(matriz=self.m1)
        datas=[x["data"] for x in r["movimentacoes"]]
        self.assertEqual(datas,sorted(datas,reverse=True))
