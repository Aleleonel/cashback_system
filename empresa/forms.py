from django import forms

from core.models import ConfiguracaoSistema
from core.choices import StatusOperacional
from empresas.models import Loja

from django.contrib.auth import get_user_model


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


class UsuarioEmpresaForm(forms.Form):

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

    lojas = forms.ModelMultipleChoiceField(
        label='Lojas',
        queryset=Loja.objects.none(),
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

    def __init__(self, *args, matriz=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.matriz = matriz
        self.usuario = usuario

        self.fields['lojas'].queryset = Loja.objects.filter(
            matriz=matriz
        ).order_by('nome')

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