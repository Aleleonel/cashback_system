from django import forms

from core.forms import BootstrapModelForm
from produtos.models import UnidadeMedida


class UnidadeMedidaForm(BootstrapModelForm):
    class Meta:
        model = UnidadeMedida

        fields = [
            'sigla',
            'descricao',
            'ativa',
        ]

        widgets = {
            'sigla': forms.TextInput(attrs={
                'placeholder': 'Ex.: UN, CX, KG',
                'maxlength': '10',
            }),
            'descricao': forms.TextInput(attrs={
                'placeholder': 'Descrição da unidade',
                'maxlength': '100',
            }),
        }

    def clean_sigla(self):
        return (
            self.cleaned_data.get('sigla') or ''
        ).strip().upper()

    def clean_descricao(self):
        return (
            self.cleaned_data.get('descricao') or ''
        ).strip()
