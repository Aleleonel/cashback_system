from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente

        fields = [
            'nome',
            'cpf',
            'telefone',
            'data_nascimento',
            'email',
            'aceita_email',
            'aceita_sms',
            'ativo',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo',
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'maxlength': '14',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(11) 99999-9999',
            }),
            'data_nascimento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'dd/mm/aaaa',
                'maxlength': '10',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'cliente@email.com',
            }),
            'aceita_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'aceita_sms': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        return ''.join(filter(str.isdigit, cpf))

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()

        if len(nome.split()) < 2:
            raise forms.ValidationError('Informe o nome completo do cliente.')

        return nome
    

class ImportarClientesForm(forms.Form):

    arquivo = forms.FileField(
        label='Planilha de clientes',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
        })
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data['arquivo']

        extensoes_permitidas = [
            '.xlsx',
            '.xls',
        ]

        if not any(arquivo.name.lower().endswith(ext) for ext in extensoes_permitidas):
            raise forms.ValidationError(
                'Envie uma planilha Excel nos formatos .xlsx ou .xls.'
            )

        return arquivo