from django import forms

from core.models import ConfiguracaoSistema
from core.choices import StatusOperacional
from empresas.models import Loja


class LojaEmpresaForm(forms.ModelForm):

    class Meta:
        model = Loja

        fields = [
            'nome',
            'cnpj',
            'telefone',
            'status',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.matriz = matriz

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')

        if not cnpj:
            return cnpj

        lojas = Loja.objects.filter(
            matriz=self.matriz,
            cnpj=cnpj
        )

        if self.instance and self.instance.pk:
            lojas = lojas.exclude(pk=self.instance.pk)

        if lojas.exists():
            raise forms.ValidationError(
                'Já existe uma loja cadastrada com este CNPJ nesta empresa.'
            )

        return cnpj
    

class ConfiguracaoCashbackEmpresaForm(forms.ModelForm):

    class Meta:
        model = ConfiguracaoSistema

        fields = [
            'percentual_cashback',
            'dias_liberacao',
            'dias_expiracao',
            'valor_minimo_compra',
            'enviar_email_saldo',
        ]

        widgets = {
            'percentual_cashback': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
            }),
            'dias_liberacao': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'dias_expiracao': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'valor_minimo_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
            }),
            'enviar_email_saldo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }