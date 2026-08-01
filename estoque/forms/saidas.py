"""Formulário de saída manual de estoque."""

from django import forms

from empresas.models import Loja
from estoque.choices import (
    NaturezaMovimentacao,
    TipoMovimentacao,
    get_natureza_tipo_movimentacao,
)
from produtos.models import Produto


def obter_tipos_saida():
    return [
        (valor, rotulo)
        for valor, rotulo in TipoMovimentacao.choices
        if get_natureza_tipo_movimentacao(valor) == NaturezaMovimentacao.SAIDA
    ]


class SaidaEstoqueForm(forms.Form):
    loja = forms.ModelChoiceField(
        label='Loja',
        queryset=Loja.objects.none(),
        empty_label='Selecione a loja',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    produto = forms.ModelChoiceField(
        label='Produto',
        queryset=Produto.objects.none(),
        empty_label='Selecione o produto',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    tipo = forms.ChoiceField(
        label='Tipo de saída',
        choices=(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    quantidade = forms.DecimalField(
        label='Quantidade',
        min_value=0.001,
        max_digits=15,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.001',
            'step': '0.001',
        }),
    )
    documento_referencia = forms.CharField(
        label='Documento de referência',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pedido, perda, consumo interno ou referência',
        }),
    )
    observacao = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
        }),
    )

    def __init__(self, *args, matriz, loja_inicial=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['loja'].queryset = Loja.objects.filter(
            matriz=matriz
        ).order_by('nome')
        self.fields['produto'].queryset = Produto.objects.filter(
            matriz=matriz,
            controla_estoque=True,
        ).order_by('nome')
        self.fields['tipo'].choices = obter_tipos_saida()

        if loja_inicial is not None:
            self.fields['loja'].initial = loja_inicial

    def clean_tipo(self):
        tipo = self.cleaned_data['tipo']
        if get_natureza_tipo_movimentacao(tipo) != NaturezaMovimentacao.SAIDA:
            raise forms.ValidationError('Selecione um tipo válido de saída.')
        return tipo