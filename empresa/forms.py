from django import forms

from core.models import ConfiguracaoSistema
from core.choices import StatusOperacional
from empresas.models import Loja
from fiscal.models_emissao_fiscal import ConfiguracaoEmissaoFiscalLoja
from accounts.permissions import get_permissoes_extras_disponiveis
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
    

class ConfiguracaoFiscalLojaEmpresaForm(forms.ModelForm):
    """Configuracao operacional de emissao NFC-e da filial."""

    CRT_CHOICES = (
        ("1", "1 - Simples Nacional"),
        ("2", "2 - Simples Nacional - excesso de sublimite"),
        ("3", "3 - Regime Normal"),
        ("4", "4 - MEI"),
    )

    crt = forms.ChoiceField(
        label="Regime tributario (CRT)",
        choices=CRT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ConfiguracaoEmissaoFiscalLoja
        fields = [
            "razao_social", "nome_fantasia", "inscricao_estadual",
            "logradouro", "numero", "complemento", "bairro", "municipio",
            "codigo_municipio_ibge", "uf", "cep", "crt", "ambiente_nfce",
            "serie_nfce", "ativa",
        ]
        labels = {
            "razao_social": "Razao social", "nome_fantasia": "Nome fantasia",
            "inscricao_estadual": "Inscricao estadual", "logradouro": "Logradouro",
            "numero": "Numero", "complemento": "Complemento", "bairro": "Bairro",
            "municipio": "Municipio", "codigo_municipio_ibge": "Codigo IBGE do municipio",
            "uf": "UF", "cep": "CEP", "ambiente_nfce": "Ambiente NFC-e",
            "serie_nfce": "Serie NFC-e", "ativa": "Configuracao fiscal ativa",
        }
        widgets = {
            "razao_social": forms.TextInput(attrs={"class": "form-control"}),
            "nome_fantasia": forms.TextInput(attrs={"class": "form-control"}),
            "inscricao_estadual": forms.TextInput(attrs={"class": "form-control"}),
            "logradouro": forms.TextInput(attrs={"class": "form-control"}),
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "complemento": forms.TextInput(attrs={"class": "form-control"}),
            "bairro": forms.TextInput(attrs={"class": "form-control"}),
            "municipio": forms.TextInput(attrs={"class": "form-control"}),
            "codigo_municipio_ibge": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "maxlength": "7"}),
            "uf": forms.TextInput(attrs={"class": "form-control text-uppercase", "maxlength": "2"}),
            "cep": forms.TextInput(attrs={"class": "form-control", "inputmode": "numeric", "maxlength": "8"}),
            "ambiente_nfce": forms.Select(attrs={"class": "form-select"}),
            "serie_nfce": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "999"}),
            "ativa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_uf(self):
        return (self.cleaned_data.get("uf") or "").strip().upper()

    def clean_cep(self):
        return "".join(c for c in (self.cleaned_data.get("cep") or "") if c.isdigit())

    def clean_codigo_municipio_ibge(self):
        return "".join(c for c in (self.cleaned_data.get("codigo_municipio_ibge") or "") if c.isdigit())


class ConfiguracaoCashbackEmpresaForm(forms.ModelForm):

    class Meta:
        model = ConfiguracaoSistema

        fields = [
            'percentual_cashback',
            'percentual_maximo_beneficio',
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
            'percentual_maximo_beneficio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
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

    def clean_percentual_maximo_beneficio(self):
        percentual = self.cleaned_data['percentual_maximo_beneficio']

        if percentual < 0 or percentual > 100:
            raise forms.ValidationError(
                'O percentual máximo de benefícios deve estar entre 0% e 100%.'
            )

        return percentual


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

    permissoes_extras = forms.MultipleChoiceField(
        label='Permissões extras',
        required=False,
        choices=[],
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, matriz=None, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.matriz = matriz
        self.usuario = usuario

        self.fields['lojas'].queryset = Loja.objects.filter(
            matriz=matriz
        ).order_by('nome')

        permissoes_disponiveis = get_permissoes_extras_disponiveis()

        self.fields['permissoes_extras'].choices = [
            (
                item['codigo'],
                f"{item['grupo']} - {item['nome']}"
            )
            for item in permissoes_disponiveis
        ]

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