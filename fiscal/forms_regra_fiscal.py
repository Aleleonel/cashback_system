from django import forms

from core.forms import BootstrapModelForm
from fiscal.models import RegraFiscal


class RegraFiscalForm(BootstrapModelForm):
    class Meta:
        model = RegraFiscal
        fields = (
            "nome",
            "codigo_interno",
            "descricao",
            "prioridade",
            "ativo",
            "matriz",
            "loja",
            "regime_tributario",
            "tipo_operacao",
            "finalidade_operacao",
            "uf_origem",
            "uf_destino",
            "contribuinte_icms",
            "consumidor_final",
            "ncm",
            "cest",
            "cfop",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
            "aliquota_icms",
            "reducao_base_icms",
            "aliquota_fcp",
            "aliquota_mva",
            "aliquota_pis",
            "aliquota_cofins",
            "aliquota_ipi",
            "diferimento_icms",
            "vigencia_inicio",
            "vigencia_fim",
        )
        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 3}
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

        for nome in (
            "contribuinte_icms",
            "consumidor_final",
        ):
            self.fields[nome].widget = forms.Select(
                choices=(
                    ("", "Qualquer"),
                    ("True", "Sim"),
                    ("False", "Nao"),
                )
            )

        for nome in (
            "aliquota_icms",
            "reducao_base_icms",
            "aliquota_fcp",
            "aliquota_mva",
            "aliquota_pis",
            "aliquota_cofins",
            "aliquota_ipi",
            "diferimento_icms",
        ):
            self.fields[nome].widget.attrs.update(
                {
                    "step": "0.0001",
                    "min": "0",
                }
            )

        self.fields["codigo_interno"].widget.attrs.update(
            {
                "maxlength": "40",
                "autocomplete": "off",
            }
        )
        self.fields["uf_origem"].widget.attrs.update(
            {"maxlength": "2"}
        )
        self.fields["uf_destino"].widget.attrs.update(
            {"maxlength": "2"}
        )

        if self.instance and self.instance.pk:
            self.fields["codigo_interno"].disabled = True
            self.fields["codigo_interno"].help_text = (
                "O codigo interno nao pode ser alterado."
            )

    def clean_codigo_interno(self):
        codigo = RegraFiscal.normalizar_codigo(
            self.cleaned_data.get("codigo_interno")
        )
        if not codigo:
            raise forms.ValidationError(
                "Informe o codigo interno."
            )
        return codigo

    def clean_uf_origem(self):
        return RegraFiscal.normalizar_uf(
            self.cleaned_data.get("uf_origem")
        )

    def clean_uf_destino(self):
        return RegraFiscal.normalizar_uf(
            self.cleaned_data.get("uf_destino")
        )
