from django import forms
from django.db.models import Q

from core.forms import BootstrapModelForm
from produtos.models import (
    Categoria,
    Marca,
    Produto,
    UnidadeMedida,
)


def somente_numeros(valor):
    return ''.join(
        caractere
        for caractere in str(valor or '')
        if caractere.isdigit()
    )


class ProdutoForm(BootstrapModelForm):
    gtin = forms.CharField(
        required=False,
        max_length=18,
        label='Código de barras GTIN/EAN',
        widget=forms.TextInput(attrs={
            'placeholder': 'Código de barras GTIN/EAN',
            'maxlength': '18',
            'inputmode': 'numeric',
        })
    )

    ncm = forms.CharField(
        required=False,
        max_length=10,
        label='NCM',
        widget=forms.TextInput(attrs={
            'placeholder': '0000.00.00',
            'maxlength': '10',
            'inputmode': 'numeric',
        })
    )

    class Meta:
        model = Produto

        fields = [
            'categoria',
            'marca',
            'unidade_medida',
            'codigo_interno',
            'sku',
            'gtin',
            'ncm',
            'nome',
            'descricao',
            'custo_base',
            'preco_venda',
            'peso_liquido_gramas',
            'peso_bruto_gramas',
            'altura_cm',
            'largura_cm',
            'comprimento_cm',
            'controla_estoque',
            'estoque_minimo',
            'status',
            "origem_mercadoria",
            "ncm_fiscal",
            "cest",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
            "regra_fiscal_padrao",
        ]

        widgets = {
            'codigo_interno': forms.TextInput(attrs={
                'placeholder': 'Código interno',
                'maxlength': '50',
            }),
            'sku': forms.TextInput(attrs={
                'placeholder': 'SKU opcional',
                'maxlength': '50',
            }),
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome comercial do produto',
                'maxlength': '150',
            }),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Descrição opcional',
                'rows': 4,
            }),
            'custo_base': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
            }),
            'preco_venda': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
            }),
            'peso_liquido_gramas': forms.NumberInput(attrs={
                'step': '1',
                'min': '0',
                'placeholder': 'Peso líquido em gramas',
            }),
            'peso_bruto_gramas': forms.NumberInput(attrs={
                'step': '1',
                'min': '0',
                'placeholder': 'Peso bruto em gramas',
            }),
            'altura_cm': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Altura em centímetros',
            }),
            'largura_cm': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Largura em centímetros',
            }),
            'comprimento_cm': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Comprimento em centímetros',
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'step': '0.001',
                'min': '0',
                'placeholder': '0,000',
            }),
        }

    def __init__(
        self,
        *args,
        matriz=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if matriz is None and self.instance.pk:
            matriz = self.instance.matriz

        self.matriz = matriz

        if matriz is not None:
            self.instance.matriz = matriz

        self._configurar_relacionamentos()
        self._configurar_campos_fiscais()

    def _configurar_relacionamentos(self):
        if self.matriz is None:
            self.fields['categoria'].queryset = (
                Categoria.objects.none()
            )
            self.fields['marca'].queryset = (
                Marca.objects.none()
            )
            self.fields['unidade_medida'].queryset = (
                UnidadeMedida.objects.none()
            )
            return

        categoria_atual_id = (
            self.instance.categoria_id
            if self.instance.pk
            else None
        )

        marca_atual_id = (
            self.instance.marca_id
            if self.instance.pk
            else None
        )

        unidade_atual_id = (
            self.instance.unidade_medida_id
            if self.instance.pk
            else None
        )

        filtro_categoria = Q(ativa=True)

        if categoria_atual_id:
            filtro_categoria |= Q(
                id=categoria_atual_id
            )

        filtro_marca = Q(ativa=True)

        if marca_atual_id:
            filtro_marca |= Q(
                id=marca_atual_id
            )

        filtro_unidade = Q(ativa=True)

        if unidade_atual_id:
            filtro_unidade |= Q(
                id=unidade_atual_id
            )

        self.fields['categoria'].queryset = (
            Categoria.objects.filter(
                matriz=self.matriz
            ).filter(
                filtro_categoria
            ).order_by(
                'nome'
            )
        )

        self.fields['marca'].queryset = (
            Marca.objects.filter(
                matriz=self.matriz
            ).filter(
                filtro_marca
            ).order_by(
                'nome'
            )
        )

        self.fields['unidade_medida'].queryset = (
            UnidadeMedida.objects.filter(
                matriz=self.matriz
            ).filter(
                filtro_unidade
            ).order_by(
                'sigla'
            )
        )

    def clean_codigo_interno(self):
        return (
            self.cleaned_data.get('codigo_interno') or ''
        ).strip().upper()

    def clean_sku(self):
        return (
            self.cleaned_data.get('sku') or ''
        ).strip().upper()

    def clean_gtin(self):
        return somente_numeros(
            self.cleaned_data.get('gtin')
        )

    def clean_ncm(self):
        return somente_numeros(
            self.cleaned_data.get('ncm')
        )

    def clean_nome(self):
        return (
            self.cleaned_data.get('nome') or ''
        ).strip()

    def clean_descricao(self):
        return (
            self.cleaned_data.get('descricao') or ''
        ).strip()

    def _clean_produto_base(self):
        dados = super().clean()

        peso_liquido = dados.get(
            'peso_liquido_gramas'
        )
        peso_bruto = dados.get(
            'peso_bruto_gramas'
        )

        if (
            peso_liquido is not None
            and peso_bruto is not None
            and peso_bruto < peso_liquido
        ):
            self.add_error(
                'peso_bruto_gramas',
                (
                    'O peso bruto não pode ser menor '
                    'que o peso líquido.'
                )
            )

        return dados

    def clean(self):
        cleaned_data = self._clean_produto_base()
        if cleaned_data is None:
            cleaned_data = self.cleaned_data
        return self._validar_configuracao_fiscal(
            cleaned_data
        )

    def _configurar_campos_fiscais(self):
        for nome in (
            "origem_mercadoria",
            "ncm_fiscal",
            "cest",
            "cst_icms",
            "csosn",
            "cst_pis",
            "cst_cofins",
            "cst_ipi",
            "beneficio_fiscal",
            "regra_fiscal_padrao",
        ):
            campo = self.fields.get(nome)
            if campo is None:
                continue
            atual_id = getattr(self.instance, f'{nome}_id', None)
            filtro = Q(ativo=True)
            if atual_id:
                filtro |= Q(pk=atual_id)
            campo.queryset = campo.queryset.filter(filtro).distinct()
            campo.required = False

    def _validar_configuracao_fiscal(self, cleaned_data):
        cst_icms = cleaned_data.get('cst_icms')
        csosn = cleaned_data.get('csosn')
        if cst_icms and csosn:
            mensagem = 'Informe CST ICMS ou CSOSN, nao os dois simultaneamente.'
            self.add_error('cst_icms', mensagem)
            self.add_error('csosn', mensagem)

        ncm = cleaned_data.get('ncm_fiscal')
        cest = cleaned_data.get('cest')
        if ncm and cest and cest.ncm_referencia and cest.ncm_referencia != ncm.codigo:
            self.add_error('cest', 'O CEST selecionado possui outro NCM de referencia.')

        return cleaned_data
