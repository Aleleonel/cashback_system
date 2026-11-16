"""Formulário de transferência de estoque entre lojas."""

from django import forms
from estoque.forms.widgets_loja_fixa import LojaOperacionalFixaWidget

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

    def __init__(self, *args, matriz, loja_inicial=None, lojas_origem_permitidas=None, fixar_loja=False, **kwargs):
        super().__init__(*args, **kwargs)
        lojas = Loja.objects.filter(matriz=matriz).order_by('nome')
        origens = lojas
        if lojas_origem_permitidas is not None:
            origens = lojas.filter(pk__in=lojas_origem_permitidas.values_list('pk', flat=True))
        self.fields['loja_origem'].queryset = origens
        self.fields['loja_destino'].queryset = lojas
        self.fields['produto'].queryset = Produto.objects.filter(
            matriz=matriz,
            controla_estoque=True,
        ).order_by('nome')

        if loja_inicial is not None:
            self.fields['loja_origem'].initial = loja_inicial
        if fixar_loja:
            lojas_validas = self.fields['loja_origem'].queryset
            if lojas_validas.count() != 1:
                raise ValueError('Loja operacional fixa exige exatamente uma loja autorizada.')
            self.fields['loja_origem'].initial = lojas_validas.get()
            self.fields['loja_origem'].widget = LojaOperacionalFixaWidget(loja_id=lojas_validas.get().pk, loja_nome=str(lojas_validas.get()))

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