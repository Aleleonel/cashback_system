from django import forms

from .models import ConfiguracaoComercial, ConfiguracaoComissaoMatriz, MetaComissaoLoja
from pdv.models import FormaPagamento


class ConfiguracaoComercialForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoComercial
        fields = (
            "cashback_ativo",
            "voucher_ativo",
            "promocoes_ativas",
            "brindes_ativos",
            "arredondamento_ativo",
        )
        labels = {
            "cashback_ativo": "Cashback ativo",
            "voucher_ativo": "Voucher ativo",
            "promocoes_ativas": "Promocoes ativas",
            "brindes_ativos": "Brindes ativos",
            "arredondamento_ativo": "Arredondamento ativo",
        }

    def __init__(self, *args, pode_editar=True, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "form-check-input"
            if not pode_editar:
                campo.disabled = True


class FormaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FormaPagamento
        fields = ("nome","codigo","tipo","ativa","permite_parcelamento","maximo_parcelas","exige_cliente_identificado","exige_autorizacao","gera_contas_receber","gera_cashback","movimenta_caixa","permite_troco","somente_funcionario")
        labels = {"nome":"Nome","codigo":"Código","tipo":"Tipo","ativa":"Ativa","permite_parcelamento":"Permite parcelamento","maximo_parcelas":"Máximo de parcelas","exige_cliente_identificado":"Exige cliente identificado","exige_autorizacao":"Exige autorização","gera_contas_receber":"Gera contas a receber","gera_cashback":"Gera cashback","movimenta_caixa":"Movimenta caixa","permite_troco":"Permite troco","somente_funcionario":"Somente funcionário"}
        widgets = {"nome":forms.TextInput(attrs={"class":"form-control"}),"codigo":forms.TextInput(attrs={"class":"form-control"}),"tipo":forms.Select(attrs={"class":"form-select"}),"maximo_parcelas":forms.NumberInput(attrs={"class":"form-control","min":"1"})}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget,forms.CheckboxInput): campo.widget.attrs["class"]="form-check-input"


class ConfiguracaoComissaoMatrizForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoComissaoMatriz
        fields = ("exigir_minimo_individual", "minimo_vendas_vendedor")


class MetaComissaoLojaForm(forms.ModelForm):
    class Meta:
        model = MetaComissaoLoja
        fields = ("valor_meta", "percentual_comissao", "ativa")
