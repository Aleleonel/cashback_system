from django import forms

from core.forms import BootstrapModelForm
from fiscal.models import NCM


class NCMForm(BootstrapModelForm):
    codigo = forms.CharField(
        required=True,
        max_length=10,
        label="Codigo",
        widget=forms.TextInput(
            attrs={
                "maxlength": "10",
                "inputmode": "numeric",
                "autocomplete": "off",
                "placeholder": "0000.00.00",
            }
        ),
    )

    class Meta:
        model = NCM
        fields = (
            "codigo",
            "descricao",
            "unidade_tributavel_padrao",
            "ativo",
        )
        widgets = {
            "descricao": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Descricao do NCM",
            }),
            "unidade_tributavel_padrao": forms.TextInput(attrs={
                "maxlength": "10",
                "placeholder": "Ex.: UN, KG ou LT",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = (
                "O codigo nao pode ser alterado."
            )

    def clean_codigo(self):
        codigo = NCM.normalizar_codigo(
            self.cleaned_data.get("codigo")
        )

        if len(codigo) != 8:
            raise forms.ValidationError(
                "Informe exatamente oito digitos."
            )

        return codigo

    def clean_descricao(self):
        descricao = (
            self.cleaned_data.get("descricao") or ""
        ).strip()

        if not descricao:
            raise forms.ValidationError(
                "Informe a descricao do NCM."
            )

        return descricao

    def clean_unidade_tributavel_padrao(self):
        return (
            self.cleaned_data.get("unidade_tributavel_padrao")
            or ""
        ).strip().upper()
