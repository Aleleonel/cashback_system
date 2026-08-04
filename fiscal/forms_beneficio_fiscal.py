from django import forms

from core.forms import BootstrapModelForm
from fiscal.models import BeneficioFiscal


class BeneficioFiscalForm(BootstrapModelForm):
    class Meta:
        model = BeneficioFiscal
        fields = (
            "codigo",
            "descricao",
            "uf",
            "tipo_beneficio",
            "fundamento_legal",
            "percentual_reducao",
            "percentual_credito",
            "exige_motivo_desoneracao",
            "motivo_desoneracao_padrao",
            "regime_tributario",
            "vigencia_inicio",
            "vigencia_fim",
            "ativo",
        )
        widgets = {
            "codigo": forms.TextInput(
                attrs={
                    "maxlength": "20",
                    "autocomplete": "off",
                }
            ),
            "descricao": forms.Textarea(
                attrs={"rows": 4}
            ),
            "fundamento_legal": forms.Textarea(
                attrs={"rows": 3}
            ),
            "vigencia_inicio": forms.DateInput(
                attrs={"type": "date"}
            ),
            "vigencia_fim": forms.DateInput(
                attrs={"type": "date"}
            ),
            "percentual_reducao": forms.NumberInput(
                attrs={
                    "step": "0.0001",
                    "min": "0",
                    "max": "100",
                }
            ),
            "percentual_credito": forms.NumberInput(
                attrs={
                    "step": "0.0001",
                    "min": "0",
                    "max": "100",
                }
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
        codigo = BeneficioFiscal.normalizar_codigo(
            self.cleaned_data.get("codigo")
        )

        if not codigo:
            raise forms.ValidationError(
                "Informe o codigo do beneficio fiscal."
            )

        return codigo

    def clean_descricao(self):
        descricao = (
            self.cleaned_data.get("descricao") or ""
        ).strip()

        if not descricao:
            raise forms.ValidationError(
                "Informe a descricao do beneficio fiscal."
            )

        return descricao

    def clean_uf(self):
        uf = BeneficioFiscal.normalizar_uf(
            self.cleaned_data.get("uf")
        )

        if uf and len(uf) != 2:
            raise forms.ValidationError(
                "Informe uma UF valida."
            )

        return uf

    def clean(self):
        dados = super().clean()
        inicio = dados.get("vigencia_inicio")
        fim = dados.get("vigencia_fim")

        if inicio and fim and fim < inicio:
            self.add_error(
                "vigencia_fim",
                "O fim da vigencia nao pode ser anterior ao inicio.",
            )

        if (
            dados.get("exige_motivo_desoneracao")
            and not (
                dados.get("motivo_desoneracao_padrao")
                or ""
            ).strip()
        ):
            self.add_error(
                "motivo_desoneracao_padrao",
                "Informe o motivo de desoneracao padrao.",
            )

        return dados
