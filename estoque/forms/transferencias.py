"""Formulário de transferência de estoque entre lojas."""

from django import forms

from empresas.models import Loja
from produtos.models import Produto


class TransferenciaEstoqueForm(forms.Form):
    loja_origem = forms.ModelChoiceField(
        label='Loja de origem',
        queryset=Loja.objects.none(),
        empty_label='Selecione a loja de origem',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    loja_destino = forms.ModelChoiceField(
        label='Loja de destino',
        queryset=Loja.objects.none(),
        empty_label='Selecione a loja de destino',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    produto = forms.ModelChoiceField(
        label='Produto',
        queryset=Produto.objects.none(),
        empty_label='Selecione o produto',
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
    motivo = forms.CharField(
        label='Motivo',
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Informe o motivo da transferência',
        }),
    )
    documento_referencia = forms.CharField(
        label='Documento de referência',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Romaneio, solicitação ou referência',
        }),
    )

    def __init__(self, *args, matriz, loja_inicial=None, **kwargs):
        super().__init__(*args, **kwargs)
        lojas = Loja.objects.filter(matriz=matriz).order_by('nome')
        self.fields['loja_origem'].queryset = lojas
        self.fields['loja_destino'].queryset = lojas
        self.fields['produto'].queryset = Produto.objects.filter(
            matriz=matriz,
            controla_estoque=True,
        ).order_by('nome')

        if loja_inicial is not None:
            self.fields['loja_origem'].initial = loja_inicial

    def clean(self):
        dados = super().clean()
        origem = dados.get('loja_origem')
        destino = dados.get('loja_destino')

        if origem is not None and destino is not None and origem.pk == destino.pk:
            self.add_error(
                'loja_destino',
                'A loja de destino deve ser diferente da loja de origem.',
            )

        return dados