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


from django.contrib.auth import get_user_model


class WizardMatrizForm(forms.Form):

    nome = forms.CharField(
        label='Nome da empresa',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    cnpj = forms.CharField(
        label='CNPJ',
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )


class WizardLojaForm(forms.Form):

    nome = forms.CharField(
        label='Nome da loja principal',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    cnpj = forms.CharField(
        label='CNPJ da loja',
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )


class WizardAdminForm(forms.Form):

    first_name = forms.CharField(
        label='Nome do administrador',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    username = forms.CharField(
        label='Usuário de acesso',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
        })
    )

    password = forms.CharField(
        label='Senha provisória',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username']

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'Já existe um usuário com este login.'
            )

        return username