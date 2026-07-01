import uuid

from django.db import models
from django.utils import timezone

from accounts.models import Usuario
from clientes.models import Cliente
from empresas.models import Loja, Matriz


class Voucher(models.Model):

    class Tipo(models.TextChoices):
        VALOR_FIXO = 'valor_fixo', 'Valor fixo'
        PERCENTUAL = 'percentual', 'Percentual'

    class Origem(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        CAMPANHA = 'campanha', 'Campanha'
        ANIVERSARIO = 'aniversario', 'Aniversário'
        IMPORTACAO = 'importacao', 'Importação'
        INDICACAO = 'indicacao', 'Indicação'
        FIDELIDADE = 'fidelidade', 'Fidelidade'

    class Status(models.TextChoices):
        ATIVO = 'ativo', 'Ativo'
        INATIVO = 'inativo', 'Inativo'

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='vouchers'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='vouchers',
        blank=True,
        null=True
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
        db_index=True
    )

    nome = models.CharField(max_length=150)

    descricao = models.TextField(
        blank=True
    )

    tipo = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        db_index=True
    )

    origem = models.CharField(
        max_length=30,
        choices=Origem.choices,
        default=Origem.MANUAL,
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ATIVO,
        db_index=True
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    data_inicio = models.DateField(
        default=timezone.localdate,
        db_index=True
    )

    data_fim = models.DateField(
        db_index=True
    )

    uso_unico_por_cliente = models.BooleanField(
        default=True
    )

    limite_utilizacao = models.PositiveIntegerField(
        default=1
    )

    total_utilizado = models.PositiveIntegerField(
        default=0
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['matriz', 'codigo']),
            models.Index(fields=['matriz', 'status']),
            models.Index(fields=['matriz', 'origem']),
            models.Index(fields=['matriz', 'cliente']),
            models.Index(fields=['matriz', 'data_inicio']),
            models.Index(fields=['matriz', 'data_fim']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(tipo='valor_fixo', valor__isnull=False, percentual__isnull=True) |
                    models.Q(tipo='percentual', percentual__isnull=False, valor__isnull=True)
                ),
                name='voucher_tipo_valor_ou_percentual'
            ),
            models.CheckConstraint(
                condition=models.Q(limite_utilizacao__gt=0),
                name='voucher_limite_utilizacao_maior_que_zero'
            ),
            models.CheckConstraint(
                condition=models.Q(total_utilizado__gte=0),
                name='voucher_total_utilizado_nao_negativo'
            ),
        ]

    def __str__(self):
        return f'{self.codigo} - {self.nome}'

    @property
    def esta_ativo(self):
        return self.status == self.Status.ATIVO

    @property
    def esta_expirado(self):
        return timezone.localdate() > self.data_fim

    @property
    def ainda_nao_iniciado(self):
        return timezone.localdate() < self.data_inicio

    @property
    def esta_esgotado(self):
        return self.total_utilizado >= self.limite_utilizacao

    @property
    def disponivel_para_uso(self):
        return (
            self.esta_ativo and
            not self.ainda_nao_iniciado and
            not self.esta_expirado and
            not self.esta_esgotado
        )


class VoucherLoja(models.Model):

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name='lojas_permitidas'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='vouchers_permitidos'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['loja__nome']
        constraints = [
            models.UniqueConstraint(
                fields=['voucher', 'loja'],
                name='uq_voucher_loja'
            )
        ]
        indexes = [
            models.Index(fields=['voucher', 'loja']),
            models.Index(fields=['loja']),
        ]

    def __str__(self):
        return f'{self.voucher.codigo} - {self.loja.nome}'


class UsoVoucher(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='usos_vouchers'
    )

    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.PROTECT,
        related_name='usos'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='usos_vouchers'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='usos_vouchers'
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='usos_vouchers'
    )

    valor_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    valor_desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    observacao = models.TextField(
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['matriz', 'cliente']),
            models.Index(fields=['matriz', 'voucher']),
            models.Index(fields=['matriz', 'loja']),
            models.Index(fields=['voucher', 'cliente']),
            models.Index(fields=['criado_em']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor_compra__gt=0),
                name='uso_voucher_valor_compra_maior_que_zero'
            ),
            models.CheckConstraint(
                condition=models.Q(valor_desconto__gt=0),
                name='uso_voucher_valor_desconto_maior_que_zero'
            ),
        ]

    def __str__(self):
        return f'{self.voucher.codigo} - {self.cliente.nome}'