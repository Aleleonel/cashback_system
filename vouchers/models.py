from django.db import models
from django.utils import timezone

from clientes.models import Cliente


class VoucherIndicacao(models.Model):

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='vouchers'
    )

    codigo = models.CharField(
        max_length=30,
        unique=True
    )

    validade = models.DateField()

    utilizado = models.BooleanField(default=False)

    utilizado_por = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vouchers_utilizados'
    )

    data_utilizacao = models.DateTimeField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    def esta_valido(self):
        return (
            not self.utilizado and
            timezone.localdate() <= self.validade
        )

    def __str__(self):
        return self.codigo