import uuid

from django.db import models
from django.utils import timezone

from empresas.models import Matriz, Loja
from clientes.models import Cliente


class LancamentoCashback(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='lancamentos_cashback'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='lancamentos_cashback'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='lancamentos_cashback'
    )

    valor_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    valor_base_cashback = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    percentual_cashback = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    valor_cashback = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    valor_utilizado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    data_compra = models.DateField(default=timezone.localdate)
    data_liberacao = models.DateField(db_index=True)
    data_expiracao = models.DateField(db_index=True)

    observacao = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_compra', '-criado_em']
        indexes = [
            models.Index(fields=['matriz', 'cliente']),
            models.Index(fields=['matriz', 'loja']),
            models.Index(fields=['matriz', 'data_liberacao']),
            models.Index(fields=['matriz', 'data_expiracao']),
            models.Index(fields=['matriz', 'cliente', 'data_liberacao']),
            models.Index(fields=['matriz', 'cliente', 'data_expiracao']),
            models.Index(fields=['cliente', 'data_compra']),
        ]

    def __str__(self):
        return f'{self.cliente.nome} - R$ {self.valor_cashback}'

    @property
    def valor_restante(self):
        return self.valor_cashback - self.valor_utilizado

    @property
    def esta_liberado(self):
        return timezone.localdate() >= self.data_liberacao

    @property
    def esta_expirado(self):
        return timezone.localdate() > self.data_expiracao

    @property
    def disponivel_para_uso(self):
        return (
            self.esta_liberado and
            not self.esta_expirado and
            self.valor_restante > 0
        )


class UsoCashback(models.Model):

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='usos_cashback'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.PROTECT,
        related_name='usos_cashback'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='usos_cashback'
    )

    valor_usado = models.DecimalField(max_digits=10, decimal_places=2)

    data_uso = models.DateTimeField(auto_now_add=True)

    observacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-data_uso']
        indexes = [
            models.Index(fields=['matriz', 'cliente']),
            models.Index(fields=['matriz', 'loja']),
            models.Index(fields=['cliente', 'data_uso']),
        ]

    def __str__(self):
        return f'{self.cliente.nome} usou R$ {self.valor_usado}'


class UsoLancamentoCashback(models.Model):

    uso_cashback = models.ForeignKey(
        UsoCashback,
        on_delete=models.CASCADE,
        related_name='itens'
    )

    lancamento = models.ForeignKey(
        LancamentoCashback,
        on_delete=models.PROTECT,
        related_name='utilizacoes'
    )

    valor_utilizado = models.DecimalField(max_digits=10, decimal_places=2)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['uso_cashback']),
            models.Index(fields=['lancamento']),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor_utilizado__gt=0),
                name='valor_utilizado_maior_que_zero'
            )
        ]

    def __str__(self):
        return f'R$ {self.valor_utilizado} do lançamento {self.lancamento_id}'