from django import forms
from django.utils import timezone

from produtos.models import Produto

from .choices import StatusFornecedor
from .models import (
    Fornecedor,
    ItemPedidoCompra,
    PedidoCompra,
)


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = [
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'inscricao_estadual',
            'telefone',
            'whatsapp',
            'email',
            'contato_principal',
            'status',
            'observacoes',
        ]

        widgets = {
            'observacoes': forms.Textarea(
                attrs={
                    'rows': 4,
                }
            ),
        }

    def clean_cnpj(self):
        return ''.join(
            caractere
            for caractere in (
                self.cleaned_data.get('cnpj') or ''
            )
            if caractere.isdigit()
        )


class PedidoCompraForm(forms.ModelForm):
    class Meta:
        model = PedidoCompra
        fields = [
            'fornecedor',
            'data_emissao',
            'previsao_entrega',
            'condicao_pagamento',
            'frete',
            'desconto',
            'observacoes',
        ]

        widgets = {
            'data_emissao': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'previsao_entrega': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'observacoes': forms.Textarea(
                attrs={'rows': 4}
            ),
        }

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound and not self.instance.pk:
            self.initial['data_emissao'] = (
                timezone.localdate()
            )

        if matriz is not None:
            self.fields['fornecedor'].queryset = (
                Fornecedor.objects.filter(
                    matriz=matriz,
                    status=StatusFornecedor.ATIVO,
                )
                .order_by('razao_social')
            )


class ItemPedidoCompraForm(forms.ModelForm):
    class Meta:
        model = ItemPedidoCompra
        fields = [
            'produto',
            'quantidade',
            'valor_unitario',
            'observacoes',
        ]

    def __init__(self, *args, matriz=None, **kwargs):
        super().__init__(*args, **kwargs)

        produtos = Produto.objects.all()

        nomes_campos = {
            campo.name
            for campo in Produto._meta.fields
        }

        if (
            matriz is not None
            and 'matriz' in nomes_campos
        ):
            produtos = produtos.filter(matriz=matriz)

        if 'ativo' in nomes_campos:
            produtos = produtos.filter(ativo=True)

        self.fields['produto'].queryset = (
            produtos.order_by('pk')
        )