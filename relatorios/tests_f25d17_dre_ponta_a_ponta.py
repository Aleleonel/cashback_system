from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from configuracoes.models import FechamentoComissao, ComissaoVendedor
from empresas.models import Matriz, Loja
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from pdv.choices import StatusOperacaoVenda
from pdv.models import Venda, ItemVenda
from produtos.models import Produto, UnidadeMedida
from relatorios.services_dre import calcular_dre


class F25D17DREPontaAPontaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        U=get_user_model()
        cls.m= Matriz.objects.create(nome="Matriz F25D17")
        cls.l= Loja.objects.create(matriz=cls.m,nome="Loja F25D17")
        cls.op=U.objects.create_user(username="f25d17_op",password="x",matriz=cls.m)
        cls.vendedor=U.objects.create_user(username="f25d17_vend",password="x",matriz=cls.m)
        cls.un=UnidadeMedida.objects.create(matriz=cls.m,sigla="UN",descricao="Unidade")
        cls.prod=Produto.objects.create(
            matriz=cls.m,unidade_medida=cls.un,codigo_interno="F25D17-P1",
            nome="Produto DRE",custo_base=Decimal("99.00"),preco_venda=Decimal("100.00"),
        )
        cls.cc=CentroCusto.objects.create(matriz=cls.m,codigo="ADM17",nome="Administrativo")
        cls.plano=PlanoConta.objects.create(
            matriz=cls.m,codigo="3.17",nome="Despesa operacional F25D17",
            tipo=PlanoConta.Tipo.ANALITICA,natureza=PlanoConta.Natureza.DESPESA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
        )
        cls.plano_fin=PlanoConta.objects.create(
            matriz=cls.m,codigo="4.17",nome="Resultado financeiro F25D17",
            tipo=PlanoConta.Tipo.ANALITICA,natureza=PlanoConta.Natureza.RECEITA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO,
        )

    def titulo(self,plano,valor,natureza,chave):
        return TituloFinanceiro.objects.create(
            matriz=self.m,loja=self.l,natureza=natureza,
            origem_tipo=TituloFinanceiro.OrigemTipo.MANUAL,origem_id=chave,
            chave_idempotencia=chave,plano_conta=plano,centro_custo=self.cc,
            descricao=chave,valor_original=Decimal(valor),valor_bruto=Decimal(valor),
            data_competencia=date(2026,10,15),data_emissao=date(2026,10,15),
            status=TituloFinanceiro.Status.ABERTO,
        )

    def test_reconciliacao_economica_completa(self):
        # Venda: subtotal 200, desconto 20, acrescimo 10 => receita liquida 190.
        v=Venda.objects.create(
            matriz=self.m,loja=self.l,operador=self.op,vendedor=self.vendedor,
            status=StatusOperacaoVenda.ABERTA,
            subtotal=Decimal("200.00"),desconto=Decimal("20.00"),
            acrescimo=Decimal("10.00"),total=Decimal("190.00"),
        )
        # Snapshot historico deliberadamente difere do custo atual do produto (99).
        i=ItemVenda.objects.create(
            venda=v,produto=self.prod,sequencia=1,quantidade=Decimal("2.000"),
            preco_unitario=Decimal("100.00"),desconto=Decimal("20.00"),
            acrescimo=Decimal("10.00"),subtotal=Decimal("200.00"),total=Decimal("190.00"),
            custo_unitario_snapshot=Decimal("40.00"),
        )
        # Item cancelado nao pode compor CMV.
        ItemVenda.objects.create(
            venda=v,produto=self.prod,sequencia=2,quantidade=Decimal("1.000"),
            preco_unitario=Decimal("999.00"),subtotal=Decimal("999.00"),
            total=Decimal("999.00"),custo_unitario_snapshot=Decimal("500.00"),
            cancelado=True,motivo_cancelamento="Fixture F25D17 item cancelado",
        )

        # Encerra depois da criacao dos itens. O update direto e intencional:
        # preserva os snapshots controlados da fixture sem executar a finalizacao real.
        Venda.objects.filter(pk=v.pk).update(
            status=StatusOperacaoVenda.FINALIZADA,
            finalizada_em=timezone.now(),
        )
        v.refresh_from_db()

        desp=self.titulo(self.plano,"30.00",TituloFinanceiro.Natureza.PAGAR,"F25D17-DESP")
        fin_rec=self.titulo(self.plano_fin,"8.00",TituloFinanceiro.Natureza.RECEBER,"F25D17-FIN-R")
        fin_pag=self.titulo(self.plano_fin,"3.00",TituloFinanceiro.Natureza.PAGAR,"F25D17-FIN-P")

        fechamento=FechamentoComissao.objects.create(
            matriz=self.m,loja=self.l,competencia_ano=2026,competencia_mes=10,
            total_vendas_loja=Decimal("190.00"),valor_meta_atingida=Decimal("0.00"),
            percentual_aplicado=Decimal("5.00"),exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        com=ComissaoVendedor.objects.create(
            fechamento=fechamento,vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid,vendedor_nome_original="Vendedor F25D17",
            total_vendas_vendedor=Decimal("190.00"),elegivel=True,valor_comissao=Decimal("10.00"),
        )

        r=calcular_dre(matriz=self.m,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.l)

        self.assertEqual(r.receita_bruta,Decimal("210.00"))
        self.assertEqual(r.deducoes_receita,Decimal("20.00"))
        self.assertEqual(r.receita_liquida,Decimal("190.00"))
        self.assertEqual(r.cmv,Decimal("80.00"))
        self.assertEqual(r.lucro_bruto,Decimal("110.00"))
        self.assertEqual(r.despesas_operacionais,Decimal("40.00"))
        self.assertEqual(r.resultado_operacional,Decimal("70.00"))
        self.assertEqual(r.resultado_financeiro,Decimal("5.00"))
        self.assertEqual(r.outras_receitas_despesas,Decimal("0.00"))
        self.assertEqual(r.resultado_antes_impostos,Decimal("75.00"))
        self.assertEqual(r.margem_bruta,Decimal("57.89473684210526315789473684"))
        self.assertEqual(r.margem_operacional,Decimal("36.84210526315789473684210526"))

        mem=r.memoria_calculo
        self.assertEqual(mem["origens_receita"],[v.pk])
        self.assertEqual(mem["origens_cmv"],[i.pk])
        self.assertEqual(set(mem["origens_despesas"]["titulos"]),{desp.pk,fin_rec.pk,fin_pag.pk})
        self.assertEqual(mem["origens_despesas"]["comissoes"],[com.pk])