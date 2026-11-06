from decimal import Decimal
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.forms import formset_factory
from clientes.models import Cliente
from empresas.models import Loja
from produtos.models import Produto
from pdv.models import FormaPagamento

class OrcamentoAtacadoCadastroForm(forms.Form):
    loja = forms.ModelChoiceField(queryset=Loja.objects.none(), label="Loja")
    vendedor = forms.ModelChoiceField(queryset=get_user_model().objects.none(), label="Vendedor")
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.none(), label="Cliente")
    validade = forms.DateField(required=False, label="Validade da proposta", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"), input_formats=["%Y-%m-%d"])
    forma_pagamento = forms.ModelChoiceField(
        queryset=FormaPagamento.objects.none(), required=False, label="Forma de pagamento",
    )
    parcelas = forms.IntegerField(min_value=1, max_value=999, initial=1, label="Parcelas")
    frete = forms.DecimalField(required=False, min_value=Decimal("0"), max_digits=14, decimal_places=2, initial=Decimal("0.00"), label="Frete (R$)", widget=forms.NumberInput(attrs={"min": "0", "step": "0.01"}))
    observacoes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Observações")

    def __init__(self, *args, matriz, lojas, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["loja"].queryset = lojas.filter(matriz=matriz).distinct()
        self.fields["cliente"].queryset = Cliente.objects.filter(matriz=matriz, ativo=True)
        self.fields["forma_pagamento"].queryset = FormaPagamento.objects.filter(
            matriz=matriz, ativa=True, somente_funcionario=False,
        ).order_by("nome")
        self.fields["forma_pagamento"].widget.attrs["data-f32-pagamento"] = "1"
        self.fields["vendedor"].queryset = get_user_model().objects.filter(
            matriz=matriz, ativo=True, is_active=True
        ).filter(Q(perfil="master") | Q(lojas__in=self.fields["loja"].queryset)).distinct().order_by("first_name", "username")
        self.fields["vendedor"].label_from_instance = lambda u: u.get_full_name() or u.username
        self._matriz = matriz
        self._lojas = self.fields["loja"].queryset
        self.fields["cliente"].widget = forms.HiddenInput(attrs={"data-f32-client-id": "1"})
        # F32M5F3D_CLIENTE: server-side queryset remains matrix-scoped.
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control" if isinstance(field.widget, forms.Textarea) else "form-select"

    def clean(self):
        cleaned = super().clean()
        vendedor, loja = cleaned.get("vendedor"), cleaned.get("loja")
        if vendedor is not None and loja is not None:
            if vendedor.matriz_id != self._matriz.pk or not (
                vendedor.perfil == "master" or vendedor.lojas.filter(pk=loja.pk).exists()
            ):
                self.add_error("vendedor", "Vendedor sem vinculo com a loja selecionada.")
        from django.utils import timezone
        validade = cleaned.get("validade")
        if validade is not None and validade < timezone.localdate():
            self.add_error("validade", "A validade nao pode estar no passado.")
        forma = cleaned.get("forma_pagamento")
        parcelas = cleaned.get("parcelas")
        if forma is not None and parcelas is not None:
            limite = forma.maximo_parcelas if forma.permite_parcelamento else 1
            if parcelas > limite:
                self.add_error("parcelas", "Quantidade acima do limite da forma selecionada.")
        elif forma is None and parcelas not in (None, 1):
            self.add_error("parcelas", "Selecione a forma de pagamento para parcelar.")
        return cleaned

class ItemOrcamentoAtacadoCadastroForm(forms.Form):
    produto = forms.ModelChoiceField(queryset=Produto.objects.none(), label="Produto")
    quantidade = forms.DecimalField(min_value=Decimal("0.001"), max_digits=12, decimal_places=3, label="Quantidade")

    def __init__(self, *args, matriz, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(matriz=matriz).order_by("nome")
        self.fields["produto"].widget = forms.HiddenInput(attrs={"data-f32-product-id": "1"})
        self.fields["quantidade"].widget.attrs.update({"class": "form-control", "step": "0.001", "min": "0.001"})

ItemOrcamentoAtacadoCadastroFormSet = formset_factory(ItemOrcamentoAtacadoCadastroForm, extra=1, can_delete=True, max_num=30, validate_max=True)
