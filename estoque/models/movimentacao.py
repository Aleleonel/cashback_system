import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from empresas.models import Loja, Matriz
from estoque.choices import (
    NaturezaMovimentacao,
    OrigemMovimentacao,
    TipoMovimentacao,
    tipo_movimentacao_compativel_com_natureza,
)
from produtos.models import Produto


TIPOS_REVERSAO = {
    TipoMovimentacao.REVERSAO_ENTRADA,
    TipoMovimentacao.REVERSAO_SAIDA,
}

TIPOS_TRANSFERENCIA = {
    TipoMovimentacao.TRANSFERENCIA_ENTRADA,
    TipoMovimentacao.TRANSFERENCIA_SAIDA,
}


class MovimentacaoEstoqueQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            'Movimentações de estoque não podem ser alteradas.'
        )

    def bulk_update(
        self,
        objs,
        fields,
        batch_size=None,
    ):
        raise ValidationError(
            'Movimentações de estoque não podem ser alteradas.'
        )

    def delete(self):
        raise ValidationError(
            'Movimentações de estoque não podem ser excluídas.'
        )


class MovimentacaoEstoque(models.Model):
    objects = MovimentacaoEstoqueQuerySet.as_manager()

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque'
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque'
    )

    tipo = models.CharField(
        max_length=40,
        choices=TipoMovimentacao.choices,
        db_index=True
    )

    natureza = models.CharField(
        max_length=10,
        choices=NaturezaMovimentacao.choices,
        db_index=True
    )

    quantidade = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal('0.001'))
        ]
    )

    saldo_anterior = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal('0.000'))
        ]
    )

    saldo_posterior = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal('0.000'))
        ]
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='movimentacoes_estoque',
        blank=True,
        null=True
    )

    observacao = models.TextField(
        blank=True
    )

    documento_referencia = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )

    origem = models.CharField(
        max_length=30,
        choices=OrigemMovimentacao.choices,
        db_index=True
    )

    origem_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )

    chave_idempotencia = models.CharField(
        max_length=150,
        blank=True,
        db_index=True
    )

    movimentacao_origem = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        related_name='reversoes',
        blank=True,
        null=True
    )

    grupo_transferencia = models.UUIDField(
        blank=True,
        null=True,
        db_index=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = [
            '-criado_em',
            '-id',
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name='mov_quantidade_positiva'
            ),
            models.CheckConstraint(
                condition=Q(saldo_anterior__gte=0),
                name='mov_saldo_anterior_nao_neg'
            ),
            models.CheckConstraint(
                condition=Q(saldo_posterior__gte=0),
                name='mov_saldo_posterior_nao_neg'
            ),
            models.UniqueConstraint(
                fields=[
                    'matriz',
                    'chave_idempotencia',
                ],
                condition=~Q(chave_idempotencia=''),
                name='uq_mov_matriz_idempotencia'
            ),
            models.UniqueConstraint(
                fields=[
                    'movimentacao_origem',
                ],
                condition=Q(
                    movimentacao_origem__isnull=False
                ),
                name='uq_mov_reversao_origem'
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    'matriz',
                    'loja',
                    'criado_em',
                ],
                name='mov_matriz_loja_data_idx'
            ),
            models.Index(
                fields=[
                    'matriz',
                    'produto',
                    'criado_em',
                ],
                name='mov_matriz_prod_data_idx'
            ),
            models.Index(
                fields=[
                    'matriz',
                    'tipo',
                    'criado_em',
                ],
                name='mov_matriz_tipo_data_idx'
            ),
            models.Index(
                fields=[
                    'matriz',
                    'natureza',
                    'criado_em',
                ],
                name='mov_matriz_nat_data_idx'
            ),
            models.Index(
                fields=[
                    'matriz',
                    'origem',
                    'origem_id',
                ],
                name='mov_matriz_origem_idx'
            ),
            models.Index(
                fields=[
                    'matriz',
                    'documento_referencia',
                ],
                name='mov_matriz_documento_idx'
            ),
        ]

    def clean(self):
        super().clean()

        erros = {}

        self._validar_relacoes(erros)
        self._validar_produto(erros)
        self._validar_quantidades(erros)
        self._validar_natureza(erros)
        self._validar_equacao_saldo(erros)
        self._validar_transferencia(erros)
        self._validar_reversao(erros)

        if erros:
            raise ValidationError(erros)

    def _validar_relacoes(self, erros):
        if (
            self.loja_id
            and self.matriz_id
            and self.loja.matriz_id != self.matriz_id
        ):
            erros['loja'] = (
                'A loja deve pertencer à mesma matriz da movimentação.'
            )

        if (
            self.produto_id
            and self.matriz_id
            and self.produto.matriz_id != self.matriz_id
        ):
            erros['produto'] = (
                'O produto deve pertencer à mesma matriz da movimentação.'
            )

    def _validar_produto(self, erros):
        if (
            self.produto_id
            and not self.produto.controla_estoque
        ):
            erros['produto'] = (
                'O produto informado não controla estoque.'
            )

    def _validar_quantidades(self, erros):
        if (
            self.quantidade is not None
            and self.quantidade <= Decimal('0.000')
        ):
            erros['quantidade'] = (
                'A quantidade da movimentação deve ser maior que zero.'
            )

        if (
            self.saldo_anterior is not None
            and self.saldo_anterior < Decimal('0.000')
        ):
            erros['saldo_anterior'] = (
                'O saldo anterior não pode ser negativo.'
            )

        if (
            self.saldo_posterior is not None
            and self.saldo_posterior < Decimal('0.000')
        ):
            erros['saldo_posterior'] = (
                'O saldo posterior não pode ser negativo.'
            )

    def _validar_natureza(self, erros):
        if (
            self.tipo
            and self.natureza
            and not tipo_movimentacao_compativel_com_natureza(
                tipo=self.tipo,
                natureza=self.natureza,
            )
        ):
            erros['natureza'] = (
                'A natureza não é compatível com o tipo da movimentação.'
            )

    def _validar_equacao_saldo(self, erros):
        campos_completos = (
            self.quantidade is not None
            and self.saldo_anterior is not None
            and self.saldo_posterior is not None
            and self.natureza
        )

        if not campos_completos:
            return

        saldo_esperado = None

        if self.natureza == NaturezaMovimentacao.ENTRADA:
            saldo_esperado = (
                self.saldo_anterior
                + self.quantidade
            )

        if self.natureza == NaturezaMovimentacao.SAIDA:
            saldo_esperado = (
                self.saldo_anterior
                - self.quantidade
            )

        if (
            saldo_esperado is not None
            and self.saldo_posterior != saldo_esperado
        ):
            erros['saldo_posterior'] = (
                'O saldo posterior não corresponde à movimentação.'
            )

    def _validar_transferencia(self, erros):
        tipo_transferencia = self.tipo in TIPOS_TRANSFERENCIA

        if (
            tipo_transferencia
            and not self.grupo_transferencia
        ):
            erros['grupo_transferencia'] = (
                'Movimentações de transferência exigem um grupo.'
            )

        if (
            not tipo_transferencia
            and self.grupo_transferencia
        ):
            erros['grupo_transferencia'] = (
                'O grupo de transferência é permitido apenas '
                'para transferências.'
            )

    def _validar_reversao(self, erros):
        tipo_reversao = self.tipo in TIPOS_REVERSAO

        if (
            tipo_reversao
            and not self.movimentacao_origem_id
        ):
            erros['movimentacao_origem'] = (
                'Uma reversão deve informar a movimentação original.'
            )

        if (
            not tipo_reversao
            and self.movimentacao_origem_id
        ):
            erros['movimentacao_origem'] = (
                'A movimentação original é permitida apenas '
                'em reversões.'
            )

        if not self.movimentacao_origem_id:
            return

        origem = self.movimentacao_origem

        self._validar_reversao_origem(erros, origem)
        self._validar_reversao_contexto(erros, origem)
        self._validar_reversao_quantidade(erros, origem)
        self._validar_reversao_tipo(erros, origem)

    def _validar_reversao_origem(self, erros, origem):
        if origem.tipo in TIPOS_REVERSAO:
            erros['movimentacao_origem'] = (
                'Não é permitido reverter outra reversão.'
            )

    def _validar_reversao_contexto(self, erros, origem):
        if (
            self.matriz_id
            and origem.matriz_id != self.matriz_id
        ):
            erros['movimentacao_origem'] = (
                'A movimentação original deve pertencer '
                'à mesma matriz.'
            )

        if (
            self.loja_id
            and origem.loja_id != self.loja_id
        ):
            erros['movimentacao_origem'] = (
                'A movimentação original deve pertencer '
                'à mesma loja.'
            )

        if (
            self.produto_id
            and origem.produto_id != self.produto_id
        ):
            erros['movimentacao_origem'] = (
                'A movimentação original deve possuir '
                'o mesmo produto.'
            )

    def _validar_reversao_quantidade(self, erros, origem):
        if (
            self.quantidade is not None
            and self.quantidade != origem.quantidade
        ):
            erros['quantidade'] = (
                'A reversão deve possuir a mesma quantidade '
                'da movimentação original.'
            )

    def _validar_reversao_tipo(self, erros, origem):
        tipo_reversao_esperado = None

        if origem.natureza == NaturezaMovimentacao.ENTRADA:
            tipo_reversao_esperado = (
                TipoMovimentacao.REVERSAO_SAIDA
            )

        if origem.natureza == NaturezaMovimentacao.SAIDA:
            tipo_reversao_esperado = (
                TipoMovimentacao.REVERSAO_ENTRADA
            )

        if (
            tipo_reversao_esperado is not None
            and self.tipo != tipo_reversao_esperado
        ):
            erros['tipo'] = (
                'O tipo da reversão não corresponde '
                'à natureza da movimentação original.'
            )

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(
                'Movimentações de estoque não podem ser alteradas.'
            )

        self._normalizar_textos()
        self.full_clean()

        super().save(*args, **kwargs)

    def _normalizar_textos(self):
        self.observacao = (
            self.observacao or ''
        ).strip()

        self.documento_referencia = (
            self.documento_referencia or ''
        ).strip()

        self.origem_id = (
            self.origem_id or ''
        ).strip()

        self.chave_idempotencia = (
            self.chave_idempotencia or ''
        ).strip()

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'Movimentações de estoque não podem ser excluídas.'
        )

    def __str__(self):
        return (
            f'{self.produto.codigo_interno} - '
            f'{self.get_tipo_display()} - '
            f'{self.quantidade}'
        )

