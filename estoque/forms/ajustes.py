"""Formulário de ajuste manual de estoque."""

from django import forms
from estoque.forms.widgets_loja_fixa import LojaOperacionalFixaWidget

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

    def __init__(self, *args, matriz, loja_inicial=None, lojas_permitidas=None, fixar_loja=False, **kwargs):
        super().__init__(*args, **kwargs)
        lojas = Loja.objects.filter(matriz=matriz)
        if lojas_permitidas is not None:
            lojas = lojas.filter(pk__in=lojas_permitidas.values_list('pk', flat=True))
        self.fields['loja'].queryset = lojas.order_by('nome')
        self.fields['produto'].queryset = Produto.objects.filter(
            matriz=matriz,
            controla_estoque=True,
        ).order_by('nome')

        if loja_inicial is not None:
            self.fields['loja'].initial = loja_inicial
        if fixar_loja:
            lojas_validas = self.fields['loja'].queryset
            if lojas_validas.count() != 1:
                raise ValueError('Loja operacional fixa exige exatamente uma loja autorizada.')
            self.fields['loja'].initial = lojas_validas.get()
            self.fields['loja'].widget = LojaOperacionalFixaWidget(loja_id=lojas_validas.get().pk, loja_nome=str(lojas_validas.get()))

    def clean_quantidade_ajuste(self):
        quantidade = self.cleaned_data['quantidade_ajuste']
        if quantidade == 0:
            raise forms.ValidationError(
                'A quantidade do ajuste não pode ser zero.'
            )
        return quantidade