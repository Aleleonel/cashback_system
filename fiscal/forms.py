from django import forms

from core.forms import BootstrapModelForm
from fiscal.models import OrigemMercadoria


class OrigemMercadoriaForm(BootstrapModelForm):
    class Meta:
        model = OrigemMercadoria
        fields = (
            "codigo",
            "descricao",
            "ativo",
        )
        widgets = {
            "codigo": forms.TextInput(
                attrs={
                    "maxlength": "1",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                    "placeholder": "0 a 8",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": "180",
                    "placeholder": "Descricao oficial da origem",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].help_text = (
                "O codigo oficial nao pode ser alterado."
            )

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip()

        if (
            len(codigo) != 1
            or not codigo.isdigit()
            or codigo not in "012345678"
        ):
            raise forms.ValidationError(
                "Informe um codigo entre 0 e 8."
            )

        return codigo

    def clean_descricao(self):
        descricao = (
            self.cleaned_data.get("descricao") or ""
        ).strip()

        if not descricao:
            raise forms.ValidationError(
                "Informe a descricao da origem."
            )

        return descricao

from fiscal.forms_cst_icms import CSTICMSForm

from fiscal.forms_csosn import CSOSNForm

from fiscal.forms_cfop import CFOPForm

from fiscal.forms_ncm import NCMForm

from fiscal.forms_cst_pis import CSTPISForm

from fiscal.forms_cst_cofins import CSTCOFINSForm

from fiscal.forms_cst_ipi import CSTIPIForm

from fiscal.forms_cest import CESTForm

from fiscal.forms_beneficio_fiscal import BeneficioFiscalForm

from fiscal.forms_regra_fiscal import RegraFiscalForm
