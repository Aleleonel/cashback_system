from django import forms

from .models import Fornecedor


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = [
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'inscricao_estadual',
            'telefone',
            'whatsapp',
            'email',
            'contato_principal',
            'status',
            'observacoes',
        ]

        widgets = {
            'observacoes': forms.Textarea(
                attrs={
                    'rows': 4,
                }
            ),
        }

    def clean_cnpj(self):
        return ''.join(
            caractere
            for caractere in (
                self.cleaned_data.get('cnpj') or ''
            )
            if caractere.isdigit()
        )