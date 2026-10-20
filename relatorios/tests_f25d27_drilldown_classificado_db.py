from datetime import date
from decimal import Decimal
from django.test import TestCase
from empresas.models import Matriz, Loja
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from relatorios.services_dre import calcular_dre, obter_drilldown_dre

class F25D27DrilldownClassificadoDBTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m=Matriz.objects.create(nome="Matriz F25D27")
        cls.l=Loja.objects.create(matriz=cls.m,nome="Loja F25D27")
        cls.cc=CentroCusto.objects.create(matriz=cls.m,codigo="CC27",nome="Centro F25D27")
        specs=[
            ("1.27","Deducao",PlanoConta.Natureza.DESPESA,PlanoConta.ClassificacaoDRE.DEDUCAO_RECEITA),
            ("3.27","Operacional",PlanoConta.Natureza.DESPESA,PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL),
            ("4.27","Financeiro",PlanoConta.Natureza.RECEITA,PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO),
            ("5.27","Outros",PlanoConta.Natureza.RECEITA,PlanoConta.ClassificacaoDRE.OUTRA_RECEITA_DESPESA),
        ]
        cls.planos={}
        for codigo,nome,natureza,classif in specs:
            cls.planos[classif]=PlanoConta.objects.create(
                matriz=cls.m,codigo=codigo,nome=nome,tipo=PlanoConta.Tipo.ANALITICA,
                natureza=natureza,classificacao_dre=classif)
    def titulo(self,classif,valor,natureza,chave):
        return TituloFinanceiro.objects.create(
            matriz=self.m,loja=self.l,natureza=natureza,origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave,chave_idempotencia=chave,plano_conta=self.planos[classif],centro_custo=self.cc,
            descricao=chave,valor_original=Decimal(valor),valor_bruto=Decimal(valor),
            data_competencia=date(2026,10,15),data_emissao=date(2026,10,15),status=TituloFinanceiro.Status.ABERTO)
    def test_memoria_e_drilldown_segregam_quatro_classificacoes_reais(self):
        ded=self.titulo(PlanoConta.ClassificacaoDRE.DEDUCAO_RECEITA,"10",TituloFinanceiro.Natureza.PAGAR,"F25D27-DED")
        op=self.titulo(PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,"20",TituloFinanceiro.Natureza.PAGAR,"F25D27-OP")
        fin=self.titulo(PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO,"30",TituloFinanceiro.Natureza.RECEBER,"F25D27-FIN")
        out=self.titulo(PlanoConta.ClassificacaoDRE.OUTRA_RECEITA_DESPESA,"40",TituloFinanceiro.Natureza.RECEBER,"F25D27-OUT")
        r=calcular_dre(matriz=self.m,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.l)
        por=r.memoria_calculo["origens_por_linha"]
        self.assertEqual(por["deducoes_receita"]["titulos"],[ded.pk])
        self.assertEqual(por["despesas_operacionais"]["titulos"],[op.pk])
        self.assertEqual(por["resultado_financeiro"]["titulos"],[fin.pk])
        self.assertEqual(por["outras_receitas_despesas"]["titulos"],[out.pk])
        self.assertEqual(obter_drilldown_dre(r,"deducoes_receita")["titulos"],[ded.pk])
        self.assertEqual(obter_drilldown_dre(r,"despesas_operacionais")["titulos"],[op.pk])
        self.assertEqual(obter_drilldown_dre(r,"resultado_financeiro")["titulos"],[fin.pk])
        self.assertEqual(obter_drilldown_dre(r,"outras_receitas_despesas")["titulos"],[out.pk])
        self.assertEqual(set(r.memoria_calculo["origens_despesas"]["titulos"]),{ded.pk,op.pk,fin.pk,out.pk})
    def test_valores_economicos_permanecem_coerentes_com_segregacao(self):
        self.titulo(PlanoConta.ClassificacaoDRE.DEDUCAO_RECEITA,"10",TituloFinanceiro.Natureza.PAGAR,"F25D27-V-DED")
        self.titulo(PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,"20",TituloFinanceiro.Natureza.PAGAR,"F25D27-V-OP")
        self.titulo(PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO,"30",TituloFinanceiro.Natureza.RECEBER,"F25D27-V-FIN")
        self.titulo(PlanoConta.ClassificacaoDRE.OUTRA_RECEITA_DESPESA,"40",TituloFinanceiro.Natureza.RECEBER,"F25D27-V-OUT")
        r=calcular_dre(matriz=self.m,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.l)
        self.assertEqual(r.deducoes_receita,Decimal("10"))
        self.assertEqual(r.despesas_operacionais,Decimal("20"))
        self.assertEqual(r.resultado_financeiro,Decimal("30"))
        self.assertEqual(r.outras_receitas_despesas,Decimal("40"))