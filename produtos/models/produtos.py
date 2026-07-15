import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from empresas.models import Matriz
from produtos.choices import OrigemPreco, StatusProduto

from .categorias import Categoria
from .marcas import Marca
from .unidades_medida import UnidadeMedida


class Produto(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='produtos'
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='produtos',
        blank=True,
        null=True
    )

    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name='produtos',
        blank=True,
        null=True
    )

    unidade_medida = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        related_name='produtos'
    )

    sku = models.CharField(
        max_length=50,
        blank=True,
        db_index=True
    )

    codigo_interno = models.CharField(
        max_length=50,
        db_index=True
    )

    gtin = models.CharField(
        max_length=14,
        blank=True,
        db_index=True,
        help_text='Código de barras GTIN/EAN.'
    )

    ncm = models.CharField(
        max_length=8,
        blank=True,
        db_index=True,
        help_text='NCM contendo até 8 números.'
    )

    nome = models.CharField(
        max_length=150,
        db_index=True
    )

    descricao = models.TextField(
        blank=True
    )

    custo_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00'))
        ]
    )

    preco_venda = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00'))
        ]
    )

    origem_preco = models.CharField(
        max_length=30,
        choices=OrigemPreco.choices,
        default=OrigemPreco.MANUAL,
        db_index=True
    )

    peso_liquido_gramas = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Peso ou conteúdo líquido do produto em gramas.'
    )

    peso_bruto_gramas = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text='Peso total do produto embalado para cálculo de frete.'
    )

    altura_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.01'))
        ]
    )

    largura_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.01'))
        ]
    )

    comprimento_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.01'))
        ]
    )

    controla_estoque = models.BooleanField(
        default=True,
        db_index=True
    )

    estoque_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[
            MinValueValidator(Decimal('0.000'))
        ]
    )

    status = models.CharField(
        max_length=20,
        choices=StatusProduto.choices,
        default=StatusProduto.ATIVO,
        db_index=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['matriz', 'codigo_interno'],
                name='uq_produto_matriz_codigo_interno'
            ),
            models.UniqueConstraint(
                fields=['matriz', 'sku'],
                condition=~Q(sku=''),
                name='uq_produto_matriz_sku_preenchido'
            ),
            models.UniqueConstraint(
                fields=['matriz', 'gtin'],
                condition=~Q(gtin=''),
                name='uq_produto_matriz_gtin_preenchido'
            ),
            models.CheckConstraint(
                condition=Q(custo_base__gte=0),
                name='produto_custo_base_nao_negativo'
            ),
            models.CheckConstraint(
                condition=Q(preco_venda__gte=0),
                name='produto_preco_venda_nao_negativo'
            ),
            models.CheckConstraint(
                condition=Q(estoque_minimo__gte=0),
                name='produto_estoque_minimo_nao_negativo'
            ),
        ]
        indexes = [
            models.Index(
                fields=['matriz', 'nome'],
                name='produto_matriz_nome_idx'
            ),
            models.Index(
                fields=['matriz', 'status'],
                name='produto_matriz_status_idx'
            ),
            models.Index(
                fields=['matriz', 'categoria'],
                name='produto_matriz_categoria_idx'
            ),
            models.Index(
                fields=['matriz', 'marca'],
                name='produto_matriz_marca_idx'
            ),
            models.Index(
                fields=['matriz', 'codigo_interno'],
                name='produto_matriz_codigo_idx'
            ),
        ]

    def clean(self):
        super().clean()

        erros = {}

        if self.categoria_id and self.categoria.matriz_id != self.matriz_id:
            erros['categoria'] = (
                'A categoria deve pertencer à mesma matriz do produto.'
            )

        if self.marca_id and self.marca.matriz_id != self.matriz_id:
            erros['marca'] = (
                'A marca deve pertencer à mesma matriz do produto.'
            )

        if (
            self.unidade_medida_id
            and self.unidade_medida.matriz_id != self.matriz_id
        ):
            erros['unidade_medida'] = (
                'A unidade de medida deve pertencer à mesma matriz do produto.'
            )

        if (
            self.peso_liquido_gramas is not None
            and self.peso_bruto_gramas is not None
            and self.peso_bruto_gramas < self.peso_liquido_gramas
        ):
            erros['peso_bruto_gramas'] = (
                'O peso bruto não pode ser menor que o peso líquido.'
            )

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.nome = (self.nome or '').strip()
        self.codigo_interno = (self.codigo_interno or '').strip().upper()
        self.sku = (self.sku or '').strip().upper()
        self.gtin = ''.join(
            filter(str.isdigit, self.gtin or '')
        )
        self.ncm = ''.join(
            filter(str.isdigit, self.ncm or '')
        )

        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def lucro_bruto_unitario(self):
        return self.preco_venda - self.custo_base

    @property
    def markup_percentual(self):
        if self.custo_base <= 0:
            return None

        return (
            (self.preco_venda / self.custo_base) - Decimal('1')
        ) * Decimal('100')

    @property
    def margem_bruta_percentual(self):
        if self.preco_venda <= 0:
            return None

        return (
            (self.preco_venda - self.custo_base)
            / self.preco_venda
        ) * Decimal('100')

    def __str__(self):
        return f'{self.codigo_interno} - {self.nome}'
