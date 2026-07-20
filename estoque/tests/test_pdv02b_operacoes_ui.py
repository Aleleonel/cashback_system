from django.template.loader import get_template
from django.test import TestCase
from django.urls import resolve, reverse

from empresas.models import Loja, Matriz
from estoque.forms import (
    AjusteEstoqueForm,
    SaidaEstoqueForm,
    TransferenciaEstoqueForm,
)
from estoque.views import (
    criar_ajuste_estoque,
    criar_saida_estoque,
    criar_transferencia_estoque,
)
from produtos.models import Produto, UnidadeMedida


class FormulariosOperacoesEstoquePdv02BTestCase(TestCase):
    def setUp(self):
        self.matriz = Matriz.objects.create(nome='Matriz PDV-02B')
        self.outra_matriz = Matriz.objects.create(nome='Outra Matriz PDV-02B')

        self.loja_origem = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Origem',
        )
        self.loja_destino = Loja.objects.create(
            matriz=self.matriz,
            nome='Loja Destino',
        )
        Loja.objects.create(
            matriz=self.outra_matriz,
            nome='Loja Outra Matriz',
        )

        unidade = UnidadeMedida.objects.create(
            matriz=self.matriz,
            sigla='UN',
            descricao='Unidade',
        )
        outra_unidade = UnidadeMedida.objects.create(
            matriz=self.outra_matriz,
            sigla='CX',
            descricao='Caixa',
        )

        self.produto = Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=unidade,
            codigo_interno='PDV02B-001',
            nome='Produto controlado',
            controla_estoque=True,
        )
        Produto.objects.create(
            matriz=self.matriz,
            unidade_medida=unidade,
            codigo_interno='PDV02B-002',
            nome='Produto não controlado',
            controla_estoque=False,
        )
        Produto.objects.create(
            matriz=self.outra_matriz,
            unidade_medida=outra_unidade,
            codigo_interno='PDV02B-003',
            nome='Produto outra matriz',
            controla_estoque=True,
        )

    def test_saida_limita_lojas_e_produtos_ao_contexto(self):
        form = SaidaEstoqueForm(matriz=self.matriz)

        self.assertQuerySetEqual(
            form.fields['loja'].queryset,
            [self.loja_destino, self.loja_origem],
            ordered=True,
        )
        self.assertQuerySetEqual(
            form.fields['produto'].queryset,
            [self.produto],
        )

    def test_transferencia_rejeita_lojas_iguais(self):
        form = TransferenciaEstoqueForm(
            {
                'loja_origem': self.loja_origem.pk,
                'loja_destino': self.loja_origem.pk,
                'produto': self.produto.pk,
                'quantidade': '2.000',
                'motivo': 'Reposição',
                'documento_referencia': '',
            },
            matriz=self.matriz,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('loja_destino', form.errors)

    def test_ajuste_rejeita_quantidade_zero(self):
        form = AjusteEstoqueForm(
            {
                'loja': self.loja_origem.pk,
                'produto': self.produto.pk,
                'quantidade_ajuste': '0.000',
                'motivo': 'Conferência',
                'documento_referencia': '',
            },
            matriz=self.matriz,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('quantidade_ajuste', form.errors)


class RotasOperacoesEstoquePdv02BTestCase(TestCase):
    def test_rota_saida_resolve_view_correta(self):
        match = resolve(reverse('estoque:criar_saida_estoque'))
        self.assertIs(match.func, criar_saida_estoque)

    def test_rota_transferencia_resolve_view_correta(self):
        match = resolve(reverse('estoque:criar_transferencia_estoque'))
        self.assertIs(match.func, criar_transferencia_estoque)

    def test_rota_ajuste_resolve_view_correta(self):
        match = resolve(reverse('estoque:criar_ajuste_estoque'))
        self.assertIs(match.func, criar_ajuste_estoque)

    def test_template_unificado_existe(self):
        template = get_template(
            'estoque/movimentacoes/operacao_form.html'
        )
        self.assertIsNotNone(template)