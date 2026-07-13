from django import forms

from core.forms import BootstrapModelForm
from produtos.models import Marca


class MarcaForm(BootstrapModelForm):
    class Meta:
        model = Marca

        fields = [
            'nome',
            'fabricante',
            'ativa',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome da marca',
                'maxlength': '100',
            }),
            'fabricante': forms.TextInput(attrs={
                'placeholder': 'Fabricante, se aplicável',
                'maxlength': '150',
            }),
        }

    def clean_nome(self):
        return (self.cleaned_data.get('nome') or '').strip()

    def clean_fabricante(self):
        return (
            self.cleaned_data.get('fabricante') or ''
        ).strip()
