from decimal import Decimal

from django import forms
from django.utils import timezone

from produtos.models import Produto

from .choices import StatusFornecedor
from .models import (
    Fornecedor,
    ItemPedidoCompra,
    PedidoCompra,
)


def aplicar_estilo_bootstrap(formulario):
    """Aplica as classes visuais padr?o aos campos Django."""

    for campo in formulario.fields.values():
        widget = campo.widget

        if isinstance(widget, forms.HiddenInput):
            continue

        classes_atuais = (
            widget.attrs.get('class', '').split()
        )

        if isinstance(widget, forms.CheckboxInput):
            classe = 'form-check-input'
        elif isinstance(widget, forms.Select):
            classe = 'form-select'
        else:
            classe = 'form-control'

        if classe not in classes_atuais:
            classes_atuais.append(classe)

        widget.attrs['class'] = ' '.join(
            classes_atuais
        )



class FornecedorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_estilo_bootstrap(self)

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
        aplicar_estilo_bootstrap(self)

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
        aplicar_estilo_bootstrap(self)

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

class RecebimentoCompraForm(forms.Form):
    loja = forms.ModelChoiceField(
        queryset=None,
        label='Loja de entrada',
    )
    documento_referencia = forms.CharField(
        required=False,
        max_length=80,
    )
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    chave_idempotencia = forms.CharField(
        widget=forms.HiddenInput(),
    )

    def __init__(
        self,
        *args,
        matriz=None,
        pedido=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        from empresas.models import Loja

        self.fields['loja'].queryset = (
            Loja.objects
            .filter(matriz=matriz)
            .order_by('nome')
        )
        self.pedido = pedido

        for item in pedido.itens.select_related(
            'produto'
        ):
            self.fields[
                f'quantidade_{item.pk}'
            ] = forms.DecimalField(
                required=False,
                min_value=Decimal('0.000'),
                max_value=item.quantidade_pendente,
                decimal_places=3,
                max_digits=12,
                initial=item.quantidade_pendente,
                label=(
                    f'{item.produto} '
                    f'(pendente: '
                    f'{item.quantidade_pendente})'
                ),
            )

    def get_itens(self):
        itens = []

        for item in self.pedido.itens.all():
            quantidade = self.cleaned_data.get(
                f'quantidade_{item.pk}'
            )

            if quantidade:
                itens.append({
                    'item_pedido_id': item.pk,
                    'quantidade': quantidade,
                })

        return itens


class DevolucaoCompraForm(forms.Form):
    documento_referencia = forms.CharField(
        required=False,
        max_length=80,
        label='Documento de referencia',
    )
    motivo = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Motivo da devolucao',
    )
    chave_idempotencia = forms.CharField(
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, recebimento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.recebimento = recebimento

        for item in recebimento.itens.select_related(
            'item_pedido__produto'
        ):
            disponivel = (
                item.quantidade
                - item.quantidade_devolvida
            )

            if disponivel <= Decimal('0.000'):
                continue

            self.fields[
                f'quantidade_{item.pk}'
            ] = forms.DecimalField(
                required=False,
                min_value=Decimal('0.000'),
                max_value=disponivel,
                decimal_places=3,
                max_digits=12,
                initial=Decimal('0.000'),
                label=(
                    f'{item.item_pedido.produto} '
                    f'(disponivel: {disponivel})'
                ),
            )

    def clean(self):
        cleaned_data = super().clean()

        if not any(
            nome.startswith('quantidade_')
            and valor
            and valor > Decimal('0.000')
            for nome, valor in cleaned_data.items()
        ):
            raise forms.ValidationError(
                'Informe ao menos uma quantidade.'
            )

        return cleaned_data

    def get_itens(self):
        itens = []

        for item in self.recebimento.itens.all():
            quantidade = self.cleaned_data.get(
                f'quantidade_{item.pk}'
            )

            if quantidade:
                itens.append({
                    'item_recebimento_id': item.pk,
                    'quantidade': quantidade,
                })

        return itens
