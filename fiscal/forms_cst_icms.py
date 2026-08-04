from django import forms
from core.forms import BootstrapModelForm
from fiscal.models import CSTICMS

class CSTICMSForm(BootstrapModelForm):
    class Meta:
        model = CSTICMS
        fields = ("codigo", "descricao", "exige_aliquota", "permite_reducao_base", "permite_diferimento", "permite_substituicao_tributaria", "ativo")
        widgets = {
            "codigo": forms.TextInput(attrs={"maxlength": "2", "inputmode": "numeric", "autocomplete": "off", "placeholder": "00"}),
            "descricao": forms.Textarea(attrs={"rows": 3, "maxlength": "220", "placeholder": "Descricao oficial do CST ICMS"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = "O codigo oficial nao pode ser alterado."

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip()
        if len(codigo) != 2 or not codigo.isdigit():
            raise forms.ValidationError("Informe exatamente dois digitos.")
        return codigo

    def clean_descricao(self):
        descricao = (self.cleaned_data.get("descricao") or "").strip()
        if not descricao:
            raise forms.ValidationError("Informe a descricao do CST ICMS.")
        return descricao
