from django import forms

from empresas.models import Matriz


class MatrizForm(forms.ModelForm):

    class Meta:
        model = Matriz

        fields = [
            'nome',
            'cnpj',
            'ativa',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'ativa': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }