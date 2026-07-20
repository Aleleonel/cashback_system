from decimal import Decimal

from django.test import TestCase

from core.choices import StatusOperacional
from empresas.models import Loja, Matriz
from estoque.models import SaldoEstoque
from estoque.selectors.dashboard import (
    get_indicadores_dashboard_estoque,
)
from produtos.models import Produto, UnidadeMedida


class DashboardEstoqueSelectorsTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz Dashboard Estoque'
        )
        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz Dashboard'
        )

        self.loja_a = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja A',
            status=StatusOperacional.ATIVA,
        )
        self.loja_b = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja B',
            status=StatusOperacional.ATIVA,
        )
        self.loja_outra = Loja.objects.create(
            matriz=self.outra_matriz,
            nome='Loja Outra Matriz',
            status=StatusOperacional.ATIVA,
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )
        self.unidade_outra = UnidadeMedida.objects.create(
            matriz=self.outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        self.produto_com_estoque = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='DASH-001',
            nome='Produto com estoque',
            controla_estoque=True,
        )
        self.produto_zerado = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='DASH-002',
            nome='Produto zerado',
            controla_estoque=True,
        )
        self.produto_sem_saldo = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='DASH-003',
            nome='Produto sem saldo',
            controla_estoque=True,
        )
        Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='DASH-004',
            nome='Produto sem controle',
            controla_estoque=False,
        )

        produto_outra_matriz = Produto.objects.create(
            matriz=self.outra_matriz,
            unidade_medida=self.unidade_outra,
            codigo_interno='OUT-DASH-001',
            nome='Produto outra matriz',
            controla_estoque=True,
        )

        SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja_a,
            produto=self.produto_com_estoque,
            quantidade_atual=Decimal('4.500'),
        )
        SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja_b,
            produto=self.produto_com_estoque,
            quantidade_atual=Decimal('2.000'),
        )
        SaldoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja_a,
            produto=self.produto_zerado,
            quantidade_atual=Decimal('0.000'),
        )
        SaldoEstoque.objects.create(
            matriz=self.outra_matriz,
            loja=self.loja_outra,
            produto=produto_outra_matriz,
            quantidade_atual=Decimal('99.000'),
        )

    def test_retorna_indicadores_consolidados_da_matriz(self):
        indicadores = get_indicadores_dashboard_estoque(
            matriz=self.matriz,
        )

        self.assertEqual(
            indicadores['saldo_consolidado'],
            Decimal('6.500'),
        )
        self.assertEqual(
            indicadores['produtos_controlados'],
            3,
        )
        self.assertEqual(
            indicadores['produtos_com_estoque'],
            1,
        )
        self.assertEqual(
            indicadores['produtos_sem_estoque'],
            2,
        )

    def test_isola_dados_de_outras_matrizes(self):
        indicadores = get_indicadores_dashboard_estoque(
            matriz=self.matriz,
        )

        self.assertNotEqual(
            indicadores['saldo_consolidado'],
            Decimal('105.500'),
        )

    def test_matriz_sem_dados_retorna_zeros(self):
        matriz_vazia = Matriz.objects.create(
            nome='Matriz sem estoque'
        )

        indicadores = get_indicadores_dashboard_estoque(
            matriz=matriz_vazia,
        )

        self.assertEqual(
            indicadores['saldo_consolidado'],
            Decimal('0'),
        )
        self.assertEqual(
            indicadores['produtos_controlados'],
            0,
        )
        self.assertEqual(
            indicadores['produtos_com_estoque'],
            0,
        )
        self.assertEqual(
            indicadores['produtos_sem_estoque'],
            0,
        )