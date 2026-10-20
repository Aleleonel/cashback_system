from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from configuracoes.models import ComissaoVendedor, FechamentoComissao
from empresas.models import Loja, Matriz
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from relatorios.services_dre import calcular_dre

D=Decimal

class F25D21SemanticaDREDBTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m=Matriz.objects.create(nome="Matriz F25D21")
        cls.l=Loja.objects.create(matriz=cls.m,nome="Loja F25D21")
        cls.cc1=CentroCusto.objects.create(matriz=cls.m,codigo="CC21A",nome="CC A")
        cls.cc2=CentroCusto.objects.create(matriz=cls.m,codigo="CC21B",nome="CC B")
        cls.p=PlanoConta.objects.create(matriz=cls.m,codigo="D21",nome="Despesa F25D21",tipo=PlanoConta.Tipo.ANALITICA,natureza=PlanoConta.Natureza.DESPESA,aceita_lancamento=True,classificacao_dre=PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL)
        cls.u=get_user_model().objects.create_user(username="f25d21",password="x",matriz=cls.m)

    def titulo(self,valor,cc,chave):
        return TituloFinanceiro.objects.create(matriz=self.m,loja=self.l,natureza=TituloFinanceiro.Natureza.PAGAR,origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,origem_id=chave,chave_idempotencia=chave,plano_conta=self.p,centro_custo=cc,descricao=chave,valor_original=D(valor),valor_bruto=D(valor),data_competencia=date(2026,10,15),data_emissao=date(2026,10,15),status=TituloFinanceiro.Status.ABERTO)

    def comissao(self,mes,valor):
        f=FechamentoComissao.objects.create(matriz=self.m,loja=self.l,competencia_ano=2026,competencia_mes=mes,total_vendas_loja=D("1000"),percentual_aplicado=D("1"))
        return ComissaoVendedor.objects.create(fechamento=f,vendedor=self.u,vendedor_uuid_original=self.u.uuid,vendedor_nome_original="F25D21",total_vendas_vendedor=D("1000"),elegivel=True,valor_comissao=D(valor))

    def test_centro_custo_filtra_apenas_titulos_classificados(self):
        a=self.titulo("30",self.cc1,"F25D21-A")
        self.titulo("70",self.cc2,"F25D21-B")
        r=calcular_dre(matriz=self.m,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.l,centro_custo=self.cc1)
        self.assertEqual(r.despesas_operacionais,D("30"))
        self.assertEqual(r.memoria_calculo["origens_despesas"]["titulos"],[a.pk])

    def test_mes_parcial_exclui_comissao_mensal(self):
        c=self.comissao(10,"40")
        r=calcular_dre(matriz=self.m,inicio=date(2026,10,15),fim=date(2026,10,20),loja=self.l)
        self.assertEqual(r.despesas_operacionais,D("0"))
        self.assertNotIn(c.pk,r.memoria_calculo["origens_despesas"]["comissoes"])

    def test_mes_completo_inclui_comissao_mensal(self):
        c=self.comissao(10,"40")
        r=calcular_dre(matriz=self.m,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.l)
        self.assertEqual(r.despesas_operacionais,D("40"))
        self.assertIn(c.pk,r.memoria_calculo["origens_despesas"]["comissoes"])

    def test_intervalo_multimensal_inclui_so_meses_inteiros(self):
        c9=self.comissao(9,"9");c10=self.comissao(10,"10");c11=self.comissao(11,"11")
        r=calcular_dre(matriz=self.m,inicio=date(2026,9,15),fim=date(2026,11,20),loja=self.l)
        self.assertEqual(r.despesas_operacionais,D("10"))
        ids=r.memoria_calculo["origens_despesas"]["comissoes"]
        self.assertEqual(ids,[c10.pk])
        self.assertNotIn(c9.pk,ids);self.assertNotIn(c11.pk,ids)