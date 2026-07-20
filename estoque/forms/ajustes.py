"""Formulário de ajuste manual de estoque."""

from django import forms

from empresas.models import Loja
from produtos.models import Produto


class AjusteEstoqueForm(forms.Form):
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
    quantidade_ajuste = forms.DecimalField(
        label='Quantidade do ajuste',
        max_digits=15,
        decimal_places=3,
        help_text='Use valor positivo para acrescentar e negativo para reduzir.',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'placeholder': 'Ex.: 5.000 ou -2.000',
        }),
    )
    motivo = forms.CharField(
        label='Motivo',
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Informe o motivo do ajuste',
        }),
    )
    documento_referencia = forms.CharField(
        label='Documento de referência',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Inventário, conferência ou referência',
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

        if loja_inicial is not None:
            self.fields['loja'].initial = loja_inicial

    def clean_quantidade_ajuste(self):
        quantidade = self.cleaned_data['quantidade_ajuste']
        if quantidade == 0:
            raise forms.ValidationError(
                'A quantidade do ajuste não pode ser zero.'
            )
        return quantidade