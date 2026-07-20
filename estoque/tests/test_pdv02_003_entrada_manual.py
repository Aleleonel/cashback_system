from django.test import TestCase
from django.urls import resolve, reverse

from empresas.models import Loja, Matriz
from estoque.choices import (
    NaturezaMovimentacao,
    TipoMovimentacao,
    get_natureza_tipo_movimentacao,
)
from estoque.forms import EntradaEstoqueForm
from estoque.views import criar_entrada_estoque
from produtos.models import Produto, UnidadeMedida


class EntradaEstoqueFormPdv02003TestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome='Matriz PDV-02.003')
        self.outra_matriz = Matriz.objects.create(nome='Outra Matriz PDV-02.003')
        self.loja = Loja.objects.create(matriz=self.matriz, nome='Loja PDV-02.003')
        Loja.objects.create(matriz=self.outra_matriz, nome='Outra Loja PDV-02.003')
        self.unidade = UnidadeMedida.objects.create(matriz=self.matriz, sigla='UN', descricao='Unidade')
        outra_unidade = UnidadeMedida.objects.create(matriz=self.outra_matriz, sigla='CX', descricao='Caixa')
        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='ENT-FORM-001',
            nome='Produto controlado',
            controla_estoque=True,
        )
        Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=self.unidade,
            codigo_interno='ENT-FORM-002',
            nome='Produto sem controle',
            controla_estoque=False,
        )
        Produto.objects.create(
            matriz=self.outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='ENT-FORM-003',
            nome='Produto outra matriz',
            controla_estoque=True,
        )

    def test_limita_lojas_e_produtos_ao_contexto(self):
        form = EntradaEstoqueForm(matriz=self.matriz)
        self.assertQuerySetEqual(form.fields['loja'].queryset, [self.loja])
        self.assertQuerySetEqual(form.fields['produto'].queryset, [self.produto])

    def test_aceita_entrada_valida(self):
        tipo_entrada = next(
            valor
            for valor, _rotulo in TipoMovimentacao.choices
            if get_natureza_tipo_movimentacao(valor)
            == NaturezaMovimentacao.ENTRADA
        )

        form = EntradaEstoqueForm(
            {
                'loja': self.loja.pk,
                'produto': self.produto.pk,
                'tipo': tipo_entrada,
                'quantidade': '2.500',
                'documento_referencia': 'NF-PDV02003',
                'observacao': 'Entrada de validação',
            },
            matriz=self.matriz,
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())


class EntradaEstoqueUrlPdv02003TestCase(TestCase):
    def test_url_resolve_para_view_de_entrada(self):
        match = resolve(reverse('estoque:criar_entrada_estoque'))
        self.assertIs(match.func, criar_entrada_estoque)
