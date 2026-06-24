from django import forms


class DisparoAniversariantesForm(forms.Form):

    enviar_email = forms.BooleanField(
        label='Enviar por e-mail',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    enviar_whatsapp = forms.BooleanField(
        label='Enviar por WhatsApp',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    enviar_sms = forms.BooleanField(
        label='Enviar por SMS',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    assunto = forms.CharField(
        label='Assunto do e-mail',
        max_length=150,
        required=False,
        initial='Feliz aniversário! Temos um presente especial para você',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    mensagem = forms.CharField(
        label='Mensagem',
        initial=(
            'Olá, {nome}! A equipe preparou uma condição especial '
            'para comemorar seu aniversário. Entre em contato e aproveite!'
        ),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
        })
    )

    def clean(self):
        cleaned_data = super().clean()

        if not any([
            cleaned_data.get('enviar_email'),
            cleaned_data.get('enviar_whatsapp'),
            cleaned_data.get('enviar_sms'),
        ]):
            raise forms.ValidationError(
                'Selecione pelo menos um canal de envio.'
            )

        return cleaned_data