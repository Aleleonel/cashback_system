from django import forms

from clientes.models import Cliente
from empresas.models import Loja
from .models import Voucher


class VoucherForm(forms.ModelForm):

    lojas = forms.ModelMultipleChoiceField(
        label='Lojas participantes',
        queryset=Loja.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
        })
    )

    class Meta:
        model = Voucher

        fields = [
            'nome',
            'descricao',
            'tipo',
            'valor',
            'percentual',
            'cliente',
            'data_inicio',
            'data_fim',
            'uso_unico_por_cliente',
            'limite_utilizacao',
            'lojas',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'uso_unico_por_cliente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'limite_utilizacao': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.matriz = matriz

        self.fields['cliente'].queryset = Cliente.objects.filter(
            matriz=matriz,
            ativo=True
        ).order_by('nome')

        self.fields['cliente'].required = False

        self.fields['lojas'].queryset = Loja.objects.filter(
            matriz=matriz
        ).order_by('nome')

        if self.instance and self.instance.pk:
            self.fields['lojas'].initial = [
                rel.loja_id
                for rel in self.instance.lojas_permitidas.all()
            ]

    def clean(self):
        dados = super().clean()

        tipo = dados.get('tipo')
        valor = dados.get('valor')
        percentual = dados.get('percentual')
        data_inicio = dados.get('data_inicio')
        data_fim = dados.get('data_fim')

        if tipo == Voucher.Tipo.VALOR_FIXO:
            if not valor:
                raise forms.ValidationError(
                    'Informe o valor do voucher.'
                )
            dados['percentual'] = None

        if tipo == Voucher.Tipo.PERCENTUAL:
            if not percentual:
                raise forms.ValidationError(
                    'Informe o percentual do voucher.'
                )
            dados['valor'] = None

        if data_inicio and data_fim and data_fim < data_inicio:
            raise forms.ValidationError(
                'A data final não pode ser anterior à data inicial.'
            )

        return dados