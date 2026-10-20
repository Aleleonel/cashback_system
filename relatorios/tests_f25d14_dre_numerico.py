from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from empresas.models import Loja, Matriz
from financeiro.models import CentroCusto, PlanoConta, TituloFinanceiro
from pdv.choices import StatusOperacaoVenda
from pdv.models import ItemVenda, Venda
from relatorios.services_dre import calcular_dre


class F25D14DRENumericoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.matriz = Matriz.objects.create(nome="Matriz DRE F25D14")
        cls.outra_matriz = Matriz.objects.create(nome="Outra Matriz DRE F25D14")
        cls.loja = Loja.objects.create(matriz=cls.matriz, nome="Loja A DRE")
        cls.loja_b = Loja.objects.create(matriz=cls.matriz, nome="Loja B DRE")
        cls.loja_outra = Loja.objects.create(matriz=cls.outra_matriz, nome="Loja Outra DRE")
        cls.operador = User.objects.create_user(username="f25d14_op", password="x", matriz=cls.matriz)
        cls.operador_outro = User.objects.create_user(username="f25d14_outro", password="x", matriz=cls.outra_matriz)

        cls.cc = CentroCusto.objects.create(matriz=cls.matriz, codigo="ADM-DRE", nome="Administrativo DRE")
        cls.cc2 = CentroCusto.objects.create(matriz=cls.matriz, codigo="COM-DRE", nome="Comercial DRE")

        cls.plano_desp = PlanoConta.objects.create(
            matriz=cls.matriz, codigo="3.1.DRE", nome="Despesa DRE",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.DESPESA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
        )
        cls.plano_fin = PlanoConta.objects.create(
            matriz=cls.matriz, codigo="4.1.DRE", nome="Financeiro DRE",
            tipo=PlanoConta.Tipo.ANALITICA, natureza=PlanoConta.Natureza.RECEITA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.RESULTADO_FINANCEIRO,
        )

    @classmethod
    def venda(cls, *, loja, subtotal, desconto="0.00", acrescimo="0.00", custo="0.00",
              data_finalizacao=None, cancelada_em=None, item_cancelado=False, operador=None):
        v = Venda.objects.create(
            matriz=loja.matriz, loja=loja, operador=operador or cls.operador,
            status=StatusOperacaoVenda.FINALIZADA,
            subtotal=Decimal(subtotal), desconto=Decimal(desconto), acrescimo=Decimal(acrescimo),
            total=Decimal(subtotal)-Decimal(desconto)+Decimal(acrescimo),
            finalizada_em=data_finalizacao or timezone.now(), cancelada_em=cancelada_em,
        )
        # Produto nao e necessario para testar o agregador se o FK aceitar fixture existente?
        # O teste deliberadamente usa o caminho real: cria produto minimo via modelos auxiliares
        # somente quando necessario no metodo de teste.
        return v

    @classmethod
    def titulo(cls, *, loja, plano, centro, valor, competencia, natureza, chave, status=None, origem=None):
        return TituloFinanceiro.objects.create(
            matriz=loja.matriz, loja=loja, natureza=natureza,
            origem_tipo=origem or TituloFinanceiro.OrigemTipo.MANUAL,
            origem_id=chave, chave_idempotencia=chave,
            plano_conta=plano, centro_custo=centro,
            descricao=chave, valor_original=Decimal(valor), valor_bruto=Decimal(valor),
            data_competencia=competencia, data_emissao=competencia,
            status=status or TituloFinanceiro.Status.ABERTO,
        )

    def test_titulos_competencia_classificacao_cancelamento_e_filtros(self):
        d=date(2026,10,15)
        self.titulo(loja=self.loja, plano=self.plano_desp, centro=self.cc, valor="100.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.PAGAR, chave="DRE-DESP-1")
        self.titulo(loja=self.loja, plano=self.plano_desp, centro=self.cc2, valor="70.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.PAGAR, chave="DRE-DESP-CC2")
        self.titulo(loja=self.loja, plano=self.plano_desp, centro=self.cc, valor="999.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.PAGAR, chave="DRE-CANCEL",
                    status=TituloFinanceiro.Status.CANCELADO)
        self.titulo(loja=self.loja, plano=self.plano_fin, centro=self.cc, valor="25.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.RECEBER, chave="DRE-FIN-REC")
        self.titulo(loja=self.loja, plano=self.plano_fin, centro=self.cc, valor="10.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.PAGAR, chave="DRE-FIN-PAG")
        r=calcular_dre(matriz=self.matriz,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.loja,centro_custo=self.cc)
        self.assertEqual(r.despesas_operacionais,Decimal("100.00"))
        self.assertEqual(r.resultado_financeiro,Decimal("15.00"))
        self.assertEqual(len(r.memoria_calculo["origens_despesas"]["titulos"]),3)

    def test_compra_recebimento_e_titulo_venda_nao_contaminam_dre(self):
        d=date(2026,10,15)
        self.titulo(loja=self.loja, plano=self.plano_desp, centro=self.cc, valor="500.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.PAGAR, chave="DRE-COMPRA",
                    origem=TituloFinanceiro.OrigemTipo.COMPRA_RECEBIMENTO)
        self.titulo(loja=self.loja, plano=self.plano_fin, centro=self.cc, valor="800.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.RECEBER, chave="DRE-VENDA-TIT",
                    origem=TituloFinanceiro.OrigemTipo.VENDA_PAGAMENTO)
        r=calcular_dre(matriz=self.matriz,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.loja)
        self.assertEqual(r.despesas_operacionais,Decimal("0.00"))
        self.assertEqual(r.resultado_financeiro,Decimal("0.00"))
        self.assertEqual(r.memoria_calculo["origens_despesas"]["titulos"],[])

    def test_formula_sem_vendas_com_despesa_e_margens_zero(self):
        d=date(2026,10,15)
        self.titulo(loja=self.loja, plano=self.plano_desp, centro=self.cc, valor="40.00", competencia=d,
                    natureza=TituloFinanceiro.Natureza.PAGAR, chave="DRE-SEM-VENDA")
        r=calcular_dre(matriz=self.matriz,inicio=date(2026,10,1),fim=date(2026,10,31),loja=self.loja)
        self.assertEqual(r.receita_liquida,Decimal("0.00"))
        self.assertEqual(r.despesas_operacionais,Decimal("40.00"))
        self.assertEqual(r.resultado_operacional,Decimal("-40.00"))
        self.assertEqual(r.margem_bruta,Decimal("0.00"))
        self.assertEqual(r.margem_operacional,Decimal("0.00"))

    def test_isolamento_matriz(self):
        plano = PlanoConta.objects.create(
            matriz=self.outra_matriz,codigo="3.OUT",nome="Nao vazar",
            tipo=PlanoConta.Tipo.ANALITICA,natureza=PlanoConta.Natureza.DESPESA,
            classificacao_dre=PlanoConta.ClassificacaoDRE.DESPESA_OPERACIONAL,
        )
        cc=CentroCusto.objects.create(matriz=self.outra_matriz,codigo="OUT",nome="Outro")
        self.titulo(loja=self.loja_outra,plano=plano,centro=cc,valor="777.00",competencia=date(2026,10,10),
                    natureza=TituloFinanceiro.Natureza.PAGAR,chave="OUT-MATRIX")
        r=calcular_dre(matriz=self.matriz,inicio=date(2026,10,1),fim=date(2026,10,31))
        self.assertEqual(r.despesas_operacionais,Decimal("0.00"))