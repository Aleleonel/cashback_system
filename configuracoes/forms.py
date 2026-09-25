from django import forms

from .models import ConfiguracaoComercial
from pdv.models import FormaPagamento


class ConfiguracaoComercialForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoComercial
        fields = (
            "atacado_ativo",
            "pedido_minimo_atacado",
            "desconto_atacado_percentual",
            "cashback_ativo",
            "voucher_ativo",
            "promocoes_ativas",
            "brindes_ativos",
            "arredondamento_ativo",
        )
        labels = {
            "atacado_ativo": "Atacado ativo",
            "pedido_minimo_atacado": "Pedido mínimo do atacado",
            "desconto_atacado_percentual": "Desconto do atacado (%)",
            "cashback_ativo": "Cashback ativo",
            "voucher_ativo": "Voucher ativo",
            "promocoes_ativas": "Promoções ativas",
            "brindes_ativos": "Brindes ativos",
            "arredondamento_ativo": "Arredondamento ativo",
        }
        widgets = {
            "pedido_minimo_atacado": forms.NumberInput(attrs={
                "class": "form-control", "min": "0", "step": "0.01"
            }),
            "desconto_atacado_percentual": forms.NumberInput(attrs={
                "class": "form-control", "min": "0", "max": "100", "step": "0.01"
            }),
        }

    def __init__(self, *args, pode_editar=True, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            if not pode_editar:
                campo.disabled = True

    def clean(self):
        dados = super().clean()
        if dados.get("atacado_ativo"):
            pedido = dados.get("pedido_minimo_atacado")
            desconto = dados.get("desconto_atacado_percentual")
            if pedido is not None and pedido <= 0:
                self.add_error(
                    "pedido_minimo_atacado",
                    "Informe um pedido mínimo maior que zero para ativar o atacado.",
                )
            if desconto is not None and desconto <= 0:
                self.add_error(
                    "desconto_atacado_percentual",
                    "Informe um desconto maior que zero para ativar o atacado.",
                )
        return dados


class FormaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FormaPagamento
        fields = ("nome","codigo","tipo","ativa","permite_parcelamento","maximo_parcelas","exige_cliente_identificado","exige_autorizacao","gera_contas_receber","movimenta_caixa","permite_troco","somente_funcionario")
        labels = {"nome":"Nome","codigo":"Código","tipo":"Tipo","ativa":"Ativa","permite_parcelamento":"Permite parcelamento","maximo_parcelas":"Máximo de parcelas","exige_cliente_identificado":"Exige cliente identificado","exige_autorizacao":"Exige autorização","gera_contas_receber":"Gera contas a receber","movimenta_caixa":"Movimenta caixa","permite_troco":"Permite troco","somente_funcionario":"Somente funcionário"}
        widgets = {"nome":forms.TextInput(attrs={"class":"form-control"}),"codigo":forms.TextInput(attrs={"class":"form-control"}),"tipo":forms.Select(attrs={"class":"form-select"}),"maximo_parcelas":forms.NumberInput(attrs={"class":"form-control","min":"1"})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget,forms.CheckboxInput): campo.widget.attrs["class"]="form-check-input"
