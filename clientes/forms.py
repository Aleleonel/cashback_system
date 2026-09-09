from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    nome = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cep = forms.CharField(
        required=False,
        max_length=9,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000', 'maxlength': '9'}),
    )
    class Meta:
        model = Cliente
        fields = [
            'tipo_pessoa', 'nome', 'cpf', 'data_nascimento',
            'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual',
            'contato_responsavel', 'telefone', 'email', 'cep', 'logradouro',
            'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'aceita_email', 'aceita_sms', 'ativo',
        ]
        widgets = {
            'tipo_pessoa': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '14'}),
            'data_nascimento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '18'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control'}),
            'contato_responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '9'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2'}),
            'aceita_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'aceita_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo_pessoa") or self.data.get("tipo_pessoa") or "PF"

        if tipo == "PJ":
            cleaned_data["cpf"] = ""
            cleaned_data["data_nascimento"] = None
            self.instance.cpf = ""
            self.instance.cpf_normalizado = ""
            self.instance.data_nascimento = None
        elif tipo == "PF":
            for campo in ("razao_social", "nome_fantasia", "cnpj", "inscricao_estadual", "contato_responsavel"):
                cleaned_data[campo] = ""
                setattr(self.instance, campo, "")
            self.instance.cnpj_normalizado = ""

        return cleaned_data

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf') or ''
        if cpf.strip().upper() == 'CONSUMIDOR':
            raise forms.ValidationError('CPF técnico CONSUMIDOR não pode ser informado no cadastro normal.')
        return ''.join(filter(str.isdigit, cpf))

    def clean_cnpj(self):
        return ''.join(filter(str.isdigit, self.cleaned_data.get('cnpj') or ''))

    def clean_cep(self):
        cep = ''.join(filter(str.isdigit, self.cleaned_data.get('cep') or ''))
        if cep and len(cep) != 8:
            raise forms.ValidationError('CEP deve conter 8 números.')
        return cep

    def clean_nome(self):
        nome = (self.cleaned_data.get("nome") or "").strip()
        tipo = self.data.get("tipo_pessoa") or self.cleaned_data.get("tipo_pessoa") or "PF"
        if tipo == "PJ":
            fantasia = (self.data.get("nome_fantasia") or self.cleaned_data.get("nome_fantasia") or "").strip()
            razao = (self.data.get("razao_social") or self.cleaned_data.get("razao_social") or "").strip()
            return nome or fantasia or razao
        if not nome:
            raise forms.ValidationError("Nome é obrigatório para pessoa física.")
        if len(nome.split()) < 2:
            raise forms.ValidationError("Informe nome e sobrenome.")
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