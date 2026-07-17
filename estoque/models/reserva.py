import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from empresas.models import Loja, Matriz
from estoque.choices import OrigemMovimentacao, StatusReservaEstoque
from produtos.models import Produto


class ReservaEstoque(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='reservas_estoque',
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='reservas_estoque',
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='reservas_estoque',
    )

    quantidade = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal('0.001')),
        ],
    )

    status = models.CharField(
        max_length=20,
        choices=StatusReservaEstoque.choices,
        default=StatusReservaEstoque.ATIVA,
        db_index=True,
    )

    origem = models.CharField(
        max_length=30,
        choices=OrigemMovimentacao.choices,
        db_index=True,
    )

    origem_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    chave_idempotencia = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
    )

    documento_referencia = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reservas_estoque',
        blank=True,
        null=True,
    )

    expira_em = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
    )

    confirmada_em = models.DateTimeField(
        blank=True,
        null=True,
    )

    liberada_em = models.DateTimeField(
        blank=True,
        null=True,
    )

    cancelada_em = models.DateTimeField(
        blank=True,
        null=True,
    )

    expirada_em = models.DateTimeField(
        blank=True,
        null=True,
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
            '-criado_em',
            '-id',
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name='res_quantidade_positiva',
            ),
            models.UniqueConstraint(
                fields=[
                    'matriz',
                    'chave_idempotencia',
                ],
                condition=~Q(chave_idempotencia=''),
                name='uq_res_matriz_idempotencia',
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'matriz',
                    'loja',
                    'status',
                ],
                name='res_matriz_loja_status_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'produto',
                    'status',
                ],
                name='res_matriz_prod_status_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'expira_em',
                ],
                name='res_matriz_expira_idx',
            ),
            models.Index(
                fields=[
                    'matriz',
                    'origem',
                    'origem_id',
                ],
                name='res_matriz_origem_idx',
            ),
        ]

    def clean(self):
        super().clean()

        erros = {}

        self._validar_relacoes(erros)
        self._validar_produto(erros)
        self._validar_quantidade(erros)
        self._validar_estado(erros)

        if erros:
            raise ValidationError(erros)

    def _validar_relacoes(self, erros):
        if (
            self.loja_id
            and self.matriz_id
            and self.loja.matriz_id != self.matriz_id
        ):
            erros['loja'] = (
                'A loja deve pertencer à mesma matriz da reserva.'
            )

        if (
            self.produto_id
            and self.matriz_id
            and self.produto.matriz_id != self.matriz_id
        ):
            erros['produto'] = (
                'O produto deve pertencer à mesma matriz da reserva.'
            )

    def _validar_produto(self, erros):
        if (
            self.produto_id
            and not self.produto.controla_estoque
        ):
            erros['produto'] = (
                'O produto informado não controla estoque.'
            )

    def _validar_quantidade(self, erros):
        if (
            self.quantidade is not None
            and self.quantidade <= Decimal('0.000')
        ):
            erros['quantidade'] = (
                'A quantidade da reserva deve ser maior que zero.'
            )

    def _validar_estado(self, erros):
        timestamps = {
            StatusReservaEstoque.CONFIRMADA: 'confirmada_em',
            StatusReservaEstoque.LIBERADA: 'liberada_em',
            StatusReservaEstoque.CANCELADA: 'cancelada_em',
            StatusReservaEstoque.EXPIRADA: 'expirada_em',
        }

        campos_encerramento = tuple(timestamps.values())

        if self.status == StatusReservaEstoque.ATIVA:
            campos_preenchidos = [
                campo
                for campo in campos_encerramento
                if getattr(self, campo)
            ]

            if campos_preenchidos:
                erros['status'] = (
                    'Uma reserva ativa não pode possuir '
                    'data de encerramento.'
                )

            return

        campo_esperado = timestamps.get(self.status)

        if not campo_esperado:
            return

        if not getattr(self, campo_esperado):
            erros[campo_esperado] = (
                'A data correspondente ao status é obrigatória.'
            )

        campos_incompativeis = [
            campo
            for campo in campos_encerramento
            if campo != campo_esperado and getattr(self, campo)
        ]

        if campos_incompativeis:
            erros['status'] = (
                'A reserva possui datas incompatíveis com o status.'
            )

    def save(self, *args, **kwargs):
        self._normalizar_textos()
        self.full_clean()

        super().save(*args, **kwargs)

    def _normalizar_textos(self):
        self.origem_id = (
            self.origem_id or ''
        ).strip()

        self.chave_idempotencia = (
            self.chave_idempotencia or ''
        ).strip()

        self.documento_referencia = (
            self.documento_referencia or ''
        ).strip()

    def __str__(self):
        return (
            f'{self.produto.codigo_interno} - '
            f'{self.loja.nome} - '
            f'{self.quantidade} - '
            f'{self.get_status_display()}'
        )
