from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.models import Usuario
from configuracoes.models import ComissaoVendedor, FechamentoComissao
from configuracoes.services_comissoes import gerar_titulo_financeiro_comissao
from empresas.models import Loja, Matriz
from financeiro.models import PlanoConta, TituloFinanceiro, ParcelaFinanceira


class F24IdempotenciaFinanceiraIntegrationTests(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome="Matriz F24 Idem", cnpj="98765432000110")
        self.loja = Loja.objects.create(matriz=self.matriz, nome="Loja F24 Idem")
        self.vendedor = Usuario.objects.create_user(
            username="vend_f24_idem", password="x", matriz=self.matriz
        )
        self.fechamento = FechamentoComissao.objects.create(
            matriz=self.matriz, loja=self.loja, competencia_ano=2026, competencia_mes=9,
            total_vendas_loja=Decimal("10000.00"), valor_meta_atingida=Decimal("10000.00"),
            percentual_aplicado=Decimal("2.0000"), exigir_minimo_individual=False,
            minimo_individual=Decimal("0.00"),
        )
        self.comissao = ComissaoVendedor.objects.create(
            fechamento=self.fechamento, vendedor=self.vendedor,
            vendedor_uuid_original=self.vendedor.uuid,
            vendedor_nome_original="Vendedor Historico F24",
            total_vendas_vendedor=Decimal("5000.00"),
            elegivel=True, valor_comissao=Decimal("100.00"),
        )
        self.plano = PlanoConta.objects.create(
            matriz=self.matriz, codigo="F24-COM", nome="Comissoes F24",
            natureza=PlanoConta.Natureza.DESPESA, tipo=PlanoConta.Tipo.ANALITICA,
            aceita_lancamento=True, ativo=True,
        )

    def test_duas_chamadas_geram_um_titulo_e_uma_parcela(self):
        a = gerar_titulo_financeiro_comissao(
            comissao=self.comissao, vencimento=date(2026,10,10)
        )
        b = gerar_titulo_financeiro_comissao(
            comissao=self.comissao, vencimento=date(2026,10,10)
        )
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(
            TituloFinanceiro.objects.filter(
                matriz=self.matriz, origem_tipo=TituloFinanceiro.OrigemTipo.COMISSAO,
                origem_id=str(self.comissao.pk)
            ).count(), 1
        )
        self.assertEqual(ParcelaFinanceira.objects.filter(titulo=a).count(), 1)
        self.assertEqual(a.valor_original, Decimal("100.00"))

    def test_repeticao_com_vencimento_divergente_nao_cria_segundo_titulo(self):
        gerar_titulo_financeiro_comissao(
            comissao=self.comissao, vencimento=date(2026,10,10)
        )
        with self.assertRaises(Exception):
            gerar_titulo_financeiro_comissao(
                comissao=self.comissao, vencimento=date(2026,10,20)
            )
        self.assertEqual(
            TituloFinanceiro.objects.filter(
                matriz=self.matriz, origem_tipo=TituloFinanceiro.OrigemTipo.COMISSAO,
                origem_id=str(self.comissao.pk)
            ).count(), 1
        )