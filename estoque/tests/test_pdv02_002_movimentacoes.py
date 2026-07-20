from decimal import Decimal

from django.test import TestCase

from empresas.models import Loja, Matriz
from estoque.choices import (
    NaturezaMovimentacao,
    OrigemMovimentacao,
    TipoMovimentacao,
)
from estoque.models import MovimentacaoEstoque
from estoque.selectors import get_movimentacoes
from produtos.models import Produto, UnidadeMedida


class GetMovimentacoesPdv02002TestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(
            nome='Matriz PDV-02.002',
        )
        self.outra_matriz = Matriz.objects.create(
            nome='Outra Matriz PDV-02.002',
        )

        self.loja = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja PDV-02.002',
        )
        self.outra_loja = Loja.objects.create(
            matriz=self.outra_matriz,
            nome='Outra Loja PDV-02.002',
        )

        self.unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )
        self.outra_unidade = UnidadeMedida.objects.create(
            matriz=self.outra_matriz,
            sigla='UN',
            descricao='Unidade',
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='WHEY-001',
            nome='Whey Teste',
            controla_estoque=True,
        )
        self.outro_produto = Produto.objects.create(
            matriz=self.outra_matriz,
            unidade_medida=self.outra_unidade,
            codigo_interno='CRE-999',
            nome='Creatina Outra Matriz',
            controla_estoque=True,
        )

        self.movimentacao = MovimentacaoEstoque.objects.create(
            matriz=self.matriz,
            loja=self.loja,
            produto=self.produto,
            tipo=TipoMovimentacao.ENTRADA_MANUAL,
            natureza=NaturezaMovimentacao.ENTRADA,
            quantidade=Decimal('5.000'),
            saldo_anterior=Decimal('0.000'),
            saldo_posterior=Decimal('5.000'),
            documento_referencia='NF-12345',
            origem=OrigemMovimentacao.MANUAL,
            origem_id='AJUSTE-ABC',
        )

        MovimentacaoEstoque.objects.create(
            matriz=self.outra_matriz,
            loja=self.outra_loja,
            produto=self.outro_produto,
            tipo=TipoMovimentacao.ENTRADA_MANUAL,
            natureza=NaturezaMovimentacao.ENTRADA,
            quantidade=Decimal('3.000'),
            saldo_anterior=Decimal('0.000'),
            saldo_posterior=Decimal('3.000'),
            documento_referencia='NF-OUTRA',
            origem=OrigemMovimentacao.MANUAL,
            origem_id='OUTRA-MATRIZ',
        )

    def test_retorna_somente_movimentacoes_da_matriz(self):
        resultado = list(
            get_movimentacoes(
                matriz=self.matriz,
            )
        )

        self.assertEqual(
            resultado,
            [self.movimentacao],
        )

    def test_busca_por_nome_do_produto(self):
        resultado = get_movimentacoes(
            matriz=self.matriz,
            busca='whey',
        )

        self.assertQuerySetEqual(
            resultado,
            [self.movimentacao],
        )

    def test_busca_por_codigo_interno_do_produto(self):
        resultado = get_movimentacoes(
            matriz=self.matriz,
            busca='WHEY-001',
        )

        self.assertQuerySetEqual(
            resultado,
            [self.movimentacao],
        )

    def test_busca_por_documento_referencia(self):
        resultado = get_movimentacoes(
            matriz=self.matriz,
            busca='12345',
        )

        self.assertQuerySetEqual(
            resultado,
            [self.movimentacao],
        )

    def test_busca_por_origem_id(self):
        resultado = get_movimentacoes(
            matriz=self.matriz,
            busca='ajuste-abc',
        )

        self.assertQuerySetEqual(
            resultado,
            [self.movimentacao],
        )

    def test_busca_sem_correspondencia_retorna_queryset_vazio(self):
        resultado = get_movimentacoes(
            matriz=self.matriz,
            busca='inexistente',
        )

        self.assertFalse(
            resultado.exists()
        )
