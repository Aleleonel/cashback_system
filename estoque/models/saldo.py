import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from empresas.models import Loja, Matriz
from produtos.models import Produto


class SaldoEstoque(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='saldos_estoque'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='saldos_estoque'
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='saldos_estoque'
    )

    quantidade_atual = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[
            MinValueValidator(Decimal('0.000'))
        ]
    )

    ultima_movimentacao_em = models.DateTimeField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            'loja__nome',
            'produto__nome',
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'matriz',
                    'loja',
                    'produto',
                ],
                name='uq_saldo_matriz_loja_produto'
            ),
            models.CheckConstraint(
                condition=Q(quantidade_atual__gte=0),
                name='saldo_quantidade_nao_negativa'
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'matriz',
                    'produto',
                ],
                name='saldo_matriz_produto_idx'
            ),
            models.Index(
                fields=[
                    'matriz',
                    'loja',
                    'quantidade_atual',
                ],
                name='saldo_loja_quantidade_idx'
            ),
            models.Index(
                fields=[
                    'loja',
                    'ultima_movimentacao_em',
                ],
                name='saldo_loja_ultima_mov_idx'
            ),
        ]

    def clean(self):
        super().clean()

        erros = {}

        if (
            self.loja_id
            and self.matriz_id
            and self.loja.matriz_id != self.matriz_id
        ):
            erros['loja'] = (
                'A loja deve pertencer à mesma matriz do saldo.'
            )

        if (
            self.produto_id
            and self.matriz_id
            and self.produto.matriz_id != self.matriz_id
        ):
            erros['produto'] = (
                'O produto deve pertencer à mesma matriz do saldo.'
            )

        if (
            self.produto_id
            and not self.produto.controla_estoque
        ):
            erros['produto'] = (
                'O produto informado não controla estoque.'
            )

        if (
            self.quantidade_atual is not None
            and self.quantidade_atual < Decimal('0.000')
        ):
            erros['quantidade_atual'] = (
                'A quantidade atual não pode ser negativa.'
            )

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.loja.nome} - '
            f'{self.produto.codigo_interno} - '
            f'{self.quantidade_atual}'
        )

