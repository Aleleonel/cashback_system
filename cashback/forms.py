from django import forms


class NovaCompraForm(forms.Form):

    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o CPF do cliente',
            'autocomplete': 'off',
        })
    )

    nome = forms.CharField(
        label='Nome do cliente',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome completo',
        })
    )

    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(11) 99999-9999',
        })
    )

    email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'cliente@email.com',
        })
    )

    data_nascimento = forms.DateField(
        label='Data de nascimento',
        required=False,
        input_formats=['%d/%m/%Y'],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'dd/mm/aaaa',
            'maxlength': '10',
        })
    )

    valor_compra = forms.DecimalField(
        label='Valor da compra',
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0,00',
            'step': '0.01',
        })
    )

    valor_cashback_usado = forms.DecimalField(
        label='Cashback utilizado',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0,00',
            'step': '0.01',
        })
    )

    aplicar_voucher = forms.BooleanField(
        label='Aplicar voucher',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    codigo_voucher = forms.CharField(
        label='Código do voucher',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o código do voucher',
            'autocomplete': 'off',
        })
    )

    aceita_email = forms.BooleanField(
        label='Cliente aceita receber e-mail',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    aceita_sms = forms.BooleanField(
        label='Cliente aceita receber SMS',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    observacao = forms.CharField(
        label='Observação',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observação interna sobre a compra',
        })
    )

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        return ''.join(filter(str.isdigit, cpf))

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()

        if len(nome.split()) < 2:
            raise forms.ValidationError('Informe o nome completo do cliente.')

        return nome

    def clean_codigo_voucher(self):
        codigo = self.cleaned_data.get('codigo_voucher', '')
        return codigo.strip().upper()

    def clean(self):
        cleaned_data = super().clean()

        aplicar_voucher = cleaned_data.get('aplicar_voucher')
        codigo_voucher = cleaned_data.get('codigo_voucher')

        if aplicar_voucher and not codigo_voucher:
            self.add_error(
                'codigo_voucher',
                'Informe o código do voucher para aplicar o benefício.'
            )

        return cleaned_data