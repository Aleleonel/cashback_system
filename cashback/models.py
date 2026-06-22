from decimal import Decimal

from django.db import models
from django.utils import timezone

from empresas.models import Matriz, Loja
from clientes.models import Cliente


class LancamentoCashback(models.Model):

    STATUS_PENDENTE = 'pendente'
    STATUS_DISPONIVEL = 'disponivel'
    STATUS_USADO = 'usado'
    STATUS_EXPIRADO = 'expirado'
    STATUS_CANCELADO = 'cancelado'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_DISPONIVEL, 'Disponível'),
        (STATUS_USADO, 'Usado'),
        (STATUS_EXPIRADO, 'Expirado'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='lancamentos_cashback'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name='lancamentos_cashback'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='lancamentos_cashback'
    )

    valor_compra = models.DecimalField(max_digits=10, decimal_places=2)
    percentual_cashback = models.DecimalField(max_digits=5, decimal_places=2)
    valor_cashback = models.DecimalField(max_digits=10, decimal_places=2)

    data_compra = models.DateField(default=timezone.localdate)
    data_liberacao = models.DateField()
    data_expiracao = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        db_index=True
    )

    observacao = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_compra', '-criado_em']
        indexes = [
            models.Index(fields=['matriz', 'cliente']),
            models.Index(fields=['matriz', 'loja']),
            models.Index(fields=['matriz', 'status']),
            models.Index(fields=['matriz', 'data_liberacao']),
            models.Index(fields=['matriz', 'data_expiracao']),
            models.Index(fields=['cliente', 'status']),
        ]

    def __str__(self):
        return f'{self.cliente.nome} - R$ {self.valor_cashback}'
    

class UsoCashback(models.Model):

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='usos_cashback'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.CASCADE,
        related_name='usos_cashback'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
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