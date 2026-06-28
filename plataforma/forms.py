from django import forms

from empresas.models import Matriz


class MatrizForm(forms.ModelForm):

    class Meta:
        model = Matriz

        fields = [
            'nome',
            'cnpj',
            'status',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }