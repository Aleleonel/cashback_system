from django import forms

from empresas.models import Loja
from pdv.models import FormaPagamento

from .models import CentroCusto, ContaFinanceira, InstituicaoBancaria, PlanoConta, TituloFinanceiro


class PlanoContaForm(forms.ModelForm):
    def __init__(self, *form_args, **form_kwargs):
        super().__init__(*form_args, **form_kwargs)
        for name in ("codigo", "nome"):
            self.fields[name].widget.attrs["class"] = "form-control"
        for name in ("tipo", "natureza", "pai"):
            self.fields[name].widget.attrs["class"] = "form-select"
        for name in ("aceita_lancamento", "ativo"):
            self.fields[name].widget.attrs["class"] = "form-check-input"
    class Meta:
        model = PlanoConta
        fields = (
            "codigo",
            "nome",
            "tipo",
            "natureza",
            "pai",
            "aceita_lancamento",
            "ativo",
        )


class CentroCustoForm(forms.ModelForm):
    def __init__(self, *form_args, **form_kwargs):
        super().__init__(*form_args, **form_kwargs)
        for name in ("codigo", "nome"):
            self.fields[name].widget.attrs["class"] = "form-control"
        self.fields["ativo"].widget.attrs["class"] = "form-check-input"
    class Meta:
        model = CentroCusto
        fields = (
            "codigo",
            "nome",
            "ativo",
        )


class InstituicaoBancariaForm(forms.ModelForm):
    def __init__(self, *form_args, **form_kwargs):
        super().__init__(*form_args, **form_kwargs)
        for name in ("codigo_bacen", "nome"):
            self.fields[name].widget.attrs["class"] = "form-control"
        self.fields["ativo"].widget.attrs["class"] = "form-check-input"
    class Meta:
        model = InstituicaoBancaria
        fields = (
            "codigo_bacen",
            "nome",
            "ativo",
        )


class ContaFinanceiraForm(forms.ModelForm):
    def __init__(self, *form_args, **form_kwargs):
        super().__init__(*form_args, **form_kwargs)
        for name in ("loja", "instituicao", "tipo"):
            self.fields[name].widget.attrs["class"] = "form-select"
        for name in ("nome", "agencia", "numero"):
            self.fields[name].widget.attrs["class"] = "form-control"
        self.fields["ativo"].widget.attrs["class"] = "form-check-input"
    class Meta:
        model = ContaFinanceira
        fields = (
            "loja",
            "instituicao",
            "nome",
            "tipo",
            "agencia",
            "numero",
            "ativo",
        )


class LancamentoManualForm(forms.Form):
    natureza = forms.ChoiceField(choices=TituloFinanceiro.Natureza.choices)
    loja = forms.ModelChoiceField(queryset=Loja.objects.none(), required=False)
    plano_conta = forms.ModelChoiceField(queryset=PlanoConta.objects.none())
    centro_custo = forms.ModelChoiceField(queryset=CentroCusto.objects.none(), required=False)

    entidade_nome = forms.CharField(max_length=255, required=False)
    documento_referencia = forms.CharField(max_length=100, required=False)

    data_emissao = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    data_competencia = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    data_vencimento = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    valor_bruto = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    valor_desconto = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0,
    )
    valor_juros = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0,
    )
    valor_final = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
        required=False,
        disabled=True,
    )

    numero_parcelas = forms.IntegerField(min_value=1, initial=1)
    observacao = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *form_args, matriz=None, lojas=None, **form_kwargs):
        super().__init__(*form_args, **form_kwargs)

        for name in ("natureza", "loja", "plano_conta", "centro_custo"):
            self.fields[name].widget.attrs["class"] = "form-select"
        for name in (
            "entidade_nome",
            "documento_referencia",
            "data_emissao",
            "data_competencia",
            "data_vencimento",
            "valor_bruto",
            "valor_desconto",
            "valor_juros",
            "valor_final",
            "numero_parcelas",
            "observacao",
        ):
            self.fields[name].widget.attrs["class"] = "form-control"

        if matriz is None:
            self.fields["plano_conta"].queryset = PlanoConta.objects.none()
            self.fields["centro_custo"].queryset = CentroCusto.objects.none()
        else:
            self.fields["plano_conta"].queryset = PlanoConta.objects.filter(
                matriz=matriz,
                ativo=True,
                tipo=PlanoConta.Tipo.ANALITICA,
                aceita_lancamento=True,
            ).order_by("codigo", "nome")
            self.fields["centro_custo"].queryset = CentroCusto.objects.filter(
                matriz=matriz,
                ativo=True,
            ).order_by("codigo", "nome")

        if lojas is None:
            self.fields["loja"].queryset = Loja.objects.none()
        else:
            self.fields["loja"].queryset = lojas.order_by("nome")

    def clean(self):
        cleaned_data = super().clean()

        valor_bruto = cleaned_data.get("valor_bruto")
        valor_desconto = cleaned_data.get("valor_desconto") or 0
        valor_juros = cleaned_data.get("valor_juros") or 0

        if valor_bruto is not None:
            valor_final = valor_bruto - valor_desconto + valor_juros
            if valor_final < 0:
                self.add_error(
                    "valor_desconto",
                    "O desconto nao pode tornar o valor final negativo.",
                )
            else:
                cleaned_data["valor_final"] = valor_final

        return cleaned_data
class BaixaDinheiroForm(forms.Form):
    valor = forms.DecimalField(max_digits=14, decimal_places=2, min_value=0.01)
    data = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    forma_pagamento = forms.ModelChoiceField(queryset=FormaPagamento.objects.none())
    conta_financeira = forms.ModelChoiceField(queryset=ContaFinanceira.objects.none(), required=False)
    observacao = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *form_args, formas_pagamento=None, contas_financeiras=None, **form_kwargs):
        super().__init__(*form_args, **form_kwargs)
        for name in ("valor", "data", "observacao"):
            self.fields[name].widget.attrs["class"] = "form-control"
        for name in ("forma_pagamento", "conta_financeira"):
            self.fields[name].widget.attrs["class"] = "form-select"
        if formas_pagamento is not None:
            self.fields["forma_pagamento"].queryset = formas_pagamento
        if contas_financeiras is not None:
            self.fields["conta_financeira"].queryset = contas_financeiras
