from django import forms
from core.forms import BootstrapModelForm
from fiscal.models import CSOSN

class CSOSNForm(BootstrapModelForm):
    class Meta:
        model = CSOSN
        fields = ("codigo", "descricao", "exige_aliquota", "permite_reducao_base", "permite_credito", "permite_substituicao_tributaria", "ativo")
        widgets = {
            "codigo": forms.TextInput(attrs={"maxlength": "3", "inputmode": "numeric", "autocomplete": "off", "placeholder": "101"}),
            "descricao": forms.Textarea(attrs={"rows": 3, "maxlength": "240", "placeholder": "Descricao oficial do CSOSN"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = "O codigo oficial nao pode ser alterado."

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip()
        if len(codigo) != 3 or not codigo.isdigit():
            raise forms.ValidationError("Informe exatamente tres digitos.")
        return codigo

    def clean_descricao(self):
        descricao = (self.cleaned_data.get("descricao") or "").strip()
        if not descricao:
            raise forms.ValidationError("Informe a descricao do CSOSN.")
        return descricao
