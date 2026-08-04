from django import forms

from core.forms import BootstrapModelForm
from fiscal.models import CEST


class CESTForm(BootstrapModelForm):
    codigo = forms.CharField(
        required=True,
        max_length=9,
        label="Codigo",
        widget=forms.TextInput(
            attrs={
                "maxlength": "9",
                "inputmode": "numeric",
                "autocomplete": "off",
                "placeholder": "00.000.00",
            }
        ),
    )
    ncm_referencia = forms.CharField(
        required=False,
        max_length=10,
        label="NCM de referencia",
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
        model = CEST
        fields = (
            "codigo",
            "descricao",
            "segmento",
            "ncm_referencia",
            "excecao",
            "versao_tabela",
            "vigencia_inicio",
            "vigencia_fim",
            "ativo",
        )
        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 4}
            ),
            "vigencia_inicio": forms.DateInput(
                attrs={"type": "date"}
            ),
            "vigencia_fim": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = (
                "O codigo nao pode ser alterado."
            )

    def clean_codigo(self):
        codigo = CEST.normalizar_codigo(
            self.cleaned_data.get("codigo")
        )
        if len(codigo) != 7:
            raise forms.ValidationError(
                "Informe exatamente sete digitos."
            )
        return codigo

    def clean_ncm_referencia(self):
        codigo = CEST.normalizar_codigo(
            self.cleaned_data.get("ncm_referencia")
        )
        if codigo and len(codigo) != 8:
            raise forms.ValidationError(
                "Informe oito digitos para o NCM."
            )
        return codigo

    def clean_descricao(self):
        descricao = (
            self.cleaned_data.get("descricao") or ""
        ).strip()
        if not descricao:
            raise forms.ValidationError(
                "Informe a descricao do CEST."
            )
        return descricao

    def clean(self):
        dados = super().clean()
        inicio = dados.get("vigencia_inicio")
        fim = dados.get("vigencia_fim")
        if inicio and fim and fim < inicio:
            self.add_error(
                "vigencia_fim",
                "O fim da vigencia nao pode ser anterior ao inicio.",
            )
        return dados
