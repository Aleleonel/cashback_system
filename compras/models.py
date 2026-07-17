import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower

from empresas.models import Matriz
from produtos.models import Produto

from .choices import (
    StatusFornecedor,
    StatusPedidoCompra,
)


class Fornecedor(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='fornecedores',
    )

    razao_social = models.CharField(
        max_length=180,
        db_index=True,
    )

    nome_fantasia = models.CharField(
        max_length=180,
        blank=True,
        db_index=True,
    )

    cnpj = models.CharField(
        max_length=14,
        blank=True,
        db_index=True,
    )

    inscricao_estadual = models.CharField(
        max_length=30,
        blank=True,
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(
        max_length=254,
        blank=True,
    )

    contato_principal = models.CharField(
        max_length=120,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=StatusFornecedor.choices,
        default=StatusFornecedor.ATIVO,
        db_index=True,
    )

    observacoes = models.TextField(
        blank=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            'razao_social',
            'id',
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'matriz',
                    'cnpj',
                ],
                condition=~models.Q(cnpj=''),
                name='unique_fornecedor_matriz_cnpj',
            ),
            models.UniqueConstraint(
                Lower('razao_social'),
                'matriz',
                name='unique_fornecedor_matriz_razao_ci',
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'matriz',
                    'status',
                ],
                name='compras_for_matriz_status_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'razao_social',
                ],
                name='compras_for_matriz_razao_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'cnpj',
                ],
                name='compras_for_matriz_cnpj_idx',
            ),
        ]

        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.nome_fantasia or self.razao_social


class PedidoCompra(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='pedidos_compra',
    )

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        related_name='pedidos_compra',
    )

    numero = models.PositiveBigIntegerField(
        editable=False,
    )

    status = models.CharField(
        max_length=20,
        choices=StatusPedidoCompra.choices,
        default=StatusPedidoCompra.RASCUNHO,
        db_index=True,
    )

    data_emissao = models.DateField(
        db_index=True,
    )

    previsao_entrega = models.DateField(
        null=True,
        blank=True,
        db_index=True,
    )

    condicao_pagamento = models.CharField(
        max_length=120,
        blank=True,
    )

    frete = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    desconto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    observacoes = models.TextField(
        blank=True,
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos_compra_criados',
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    enviado_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelado_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            '-data_emissao',
            '-numero',
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'matriz',
                    'numero',
                ],
                name='unique_pedido_compra_matriz_numero',
            ),
            models.CheckConstraint(
                condition=models.Q(frete__gte=0),
                name='pedido_compra_frete_nao_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(desconto__gte=0),
                name='pedido_compra_desconto_nao_negativo',
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'matriz',
                    'status',
                    'data_emissao',
                ],
                name='compras_ped_mat_status_dt_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'fornecedor',
                ],
                name='compras_ped_matriz_fornec_idx',
            ),
        ]

        verbose_name = 'Pedido de compra'
        verbose_name_plural = 'Pedidos de compra'

    def __str__(self):
        return f'PC-{self.numero:06d}'

    @property
    def subtotal(self):
        return sum(
            (
                item.subtotal
                for item in self.itens.all()
            ),
            Decimal('0.00'),
        )

    @property
    def total(self):
        total = (
            self.subtotal
            + self.frete
            - self.desconto
        )

        return max(
            total,
            Decimal('0.00'),
        )


class ItemPedidoCompra(models.Model):
    pedido = models.ForeignKey(
        PedidoCompra,
        on_delete=models.CASCADE,
        related_name='itens',
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='itens_pedido_compra',
    )

    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal('0.001')),
        ],
    )

    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
        ],
    )

    quantidade_recebida = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[
            MinValueValidator(Decimal('0.000')),
        ],
    )

    observacoes = models.CharField(
        max_length=255,
        blank=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            'id',
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'pedido',
                    'produto',
                ],
                name='unique_item_pedido_compra_produto',
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0),
                name='item_pedido_quantidade_positiva',
            ),
            models.CheckConstraint(
                condition=models.Q(valor_unitario__gte=0),
                name='item_pedido_valor_nao_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade_recebida__gte=0),
                name='item_pedido_recebido_nao_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(
                    quantidade_recebida__lte=models.F('quantidade')
                ),
                name='item_pedido_recebido_ate_quantidade',
            ),
        ]

        verbose_name = 'Item do pedido de compra'
        verbose_name_plural = 'Itens do pedido de compra'

    def __str__(self):
        return f'{self.pedido} - {self.produto}'

    @property
    def subtotal(self):
        return self.quantidade * self.valor_unitario

    @property
    def quantidade_pendente(self):
        return self.quantidade - self.quantidade_recebida