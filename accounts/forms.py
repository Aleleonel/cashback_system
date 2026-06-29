from django import forms
from django.contrib.auth import get_user_model

from empresas.models import Loja, Matriz


class UsuarioPlataformaForm(forms.Form):

    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    username = forms.CharField(
        label='Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    perfil = forms.ChoiceField(
        label='Perfil',
        choices=get_user_model().PERFIL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    matriz = forms.ModelChoiceField(
        label='Matriz',
        queryset=Matriz.objects.order_by('nome'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    lojas = forms.ModelMultipleChoiceField(
        label='Lojas',
        queryset=Loja.objects.select_related('matriz').order_by('matriz__nome', 'nome'),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )

    ativo = forms.BooleanField(
        label='Usuário ativo',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    password = forms.CharField(
        label='Senha provisória',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.usuario = usuario

        if not usuario:
            self.fields['password'].required = True

    def clean_username(self):
        username = self.cleaned_data['username']

        User = get_user_model()

        usuarios = User.objects.filter(username=username)

        if self.usuario:
            usuarios = usuarios.exclude(pk=self.usuario.pk)

        if usuarios.exists():
            raise forms.ValidationError('Já existe um usuário com este login.')

        return username

    def clean(self):
        dados = super().clean()

        matriz = dados.get('matriz')
        lojas = dados.get('lojas')

        if matriz and lojas:
            for loja in lojas:
                if loja.matriz_id != matriz.id:
                    raise forms.ValidationError(
                        'Todas as lojas selecionadas devem pertencer à matriz escolhida.'
                    )

        return dados