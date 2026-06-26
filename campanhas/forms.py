from django import forms

from .models import (
    ConfiguracaoCampanhaAniversario,
    TemplateCampanha,
)

class DisparoAniversariantesForm(forms.Form):

    template = forms.ModelChoiceField(
        label='Template de campanha',
        queryset=TemplateCampanha.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

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
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )

    mensagem = forms.CharField(
        label='Mensagem',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
        })
    )

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)

        if matriz:
            self.fields['template'].queryset = TemplateCampanha.objects.filter(
                matriz=matriz,
                ativo=True
            ).order_by('nome')

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
    

class ConfiguracaoCampanhaAniversarioForm(forms.ModelForm):

    class Meta:
        model = ConfiguracaoCampanhaAniversario

        fields = [
            'ativa',
            'canal_padrao',
            'assunto_padrao',
            'mensagem_padrao',
        ]

        widgets = {
            'ativa': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'canal_padrao': forms.Select(attrs={
                'class': 'form-select',
            }),
            'assunto_padrao': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'mensagem_padrao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
            }),
        }


class TemplateCampanhaForm(forms.ModelForm):

    class Meta:
        model = TemplateCampanha

        fields = [
            'nome',
            'tipo',
            'canal',
            'ativo',
            'assunto',
            'mensagem',
        ]

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select',
            }),
            'canal': forms.Select(attrs={
                'class': 'form-select',
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'assunto': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
            }),
        }