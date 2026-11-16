from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from .models import ConfiguracaoComercial, FaixaAtacado

class PoliticaAtacadoForm(forms.ModelForm):
    class Meta:
        model=ConfiguracaoComercial
        fields=("atacado_ativo","pedido_minimo_atacado","produto_promocional_conta_para_faixa_atacado","prazo_validade_orcamento_atacado_dias")
        labels={
            "atacado_ativo":"Atacado ativo",
            "prazo_validade_orcamento_atacado_dias":"Validade padrão dos orçamentos (dias corridos)",
            "pedido_minimo_atacado":"Pedido minimo para pedidos de atacado (R$)",
            "produto_promocional_conta_para_faixa_atacado":"Produtos promocionais contam para atingir a faixa de atacado",
        }
    def clean_prazo_validade_orcamento_atacado_dias(self):
        dias = self.cleaned_data["prazo_validade_orcamento_atacado_dias"]
        if not 1 <= dias <= 365:
            raise forms.ValidationError("Informe um prazo entre 1 e 365 dias corridos.")
        return dias

    def __init__(self,*args,pode_editar=True,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["pedido_minimo_atacado"].widget.attrs.update({"class":"form-control", "min":"0", "step":"0.01"})
        self.fields["prazo_validade_orcamento_atacado_dias"].widget.attrs.update({"class":"form-control", "min":"1", "max":"365", "step":"1"})
        for campo in self.fields.values():
            if isinstance(campo.widget,forms.CheckboxInput): campo.widget.attrs["class"]="form-check-input"
            if not pode_editar: campo.disabled=True

class BaseFaixaAtacadoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        intervalos=[]
        for form in self.forms:
            if not hasattr(form,"cleaned_data") or form.cleaned_data.get("DELETE"): continue
            minimo=form.cleaned_data.get("valor_minimo"); maximo=form.cleaned_data.get("valor_maximo")
            if minimo is not None: intervalos.append((minimo,maximo,form))
        intervalos.sort(key=lambda item:item[0])
        for i in range(1,len(intervalos)):
            minimo_atual,_,_=intervalos[i]; _,maximo_anterior,_=intervalos[i-1]
            if maximo_anterior is None or minimo_atual<=maximo_anterior:
                raise forms.ValidationError("As faixas de atacado nao podem se sobrepor.")

FaixaAtacadoFormSet=inlineformset_factory(
    ConfiguracaoComercial,FaixaAtacado,formset=BaseFaixaAtacadoFormSet,
    fields=("valor_minimo","valor_maximo","percentual_desconto"),extra=1,can_delete=True,
    widgets={
        "valor_minimo":forms.NumberInput(attrs={"class":"form-control","min":"0","step":"0.01"}),
        "valor_maximo":forms.NumberInput(attrs={"class":"form-control","min":"0","step":"0.01"}),
        "percentual_desconto":forms.NumberInput(attrs={"class":"form-control","min":"0","max":"100","step":"0.01"}),
    },
)
