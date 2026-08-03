from django import forms
from core.forms import BootstrapModelForm
from fiscal.models import CFOP


class CFOPForm(BootstrapModelForm):
    class Meta:
        model = CFOP
        fields = (
            "codigo",
            "descricao",
            "gera_movimento_estoque",
            "permite_devolucao",
            "permite_remessa",
            "ativo",
        )
        widgets = {
            "codigo": forms.TextInput(attrs={
                "maxlength": "4",
                "inputmode": "numeric",
                "autocomplete": "off",
                "placeholder": "5102",
            }),
            "descricao": forms.Textarea(attrs={
                "rows": 3,
                "maxlength": "260",
                "placeholder": "Descricao oficial do CFOP",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = "O codigo oficial nao pode ser alterado."

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip()
        CFOP.classificar_codigo(codigo)
        return codigo

    def clean_descricao(self):
        descricao = (self.cleaned_data.get("descricao") or "").strip()
        if not descricao:
            raise forms.ValidationError("Informe a descricao do CFOP.")
        return descricao
