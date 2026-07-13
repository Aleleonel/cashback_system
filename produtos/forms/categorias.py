from django import forms

from core.forms import BootstrapModelForm
from produtos.models import Categoria


class CategoriaForm(BootstrapModelForm):
    class Meta:
        model = Categoria

        fields = [
            'nome',
            'descricao',
            'ativa',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome da categoria',
                'maxlength': '100',
            }),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Descrição opcional',
                'rows': 3,
            }),
        }

    def clean_nome(self):
        return (self.cleaned_data.get('nome') or '').strip()

    def clean_descricao(self):
        return (
            self.cleaned_data.get('descricao') or ''
        ).strip()
