from django.db import models

from empresas.models import Matriz


class ConfiguracaoSistema(models.Model):

    matriz = models.OneToOneField(
        Matriz,
        on_delete=models.CASCADE
    )

    percentual_cashback = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5
    )

    dias_liberacao = models.PositiveIntegerField(
        default=7
    )

    dias_expiracao = models.PositiveIntegerField(
        default=45
    )

    valor_minimo_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    texto_email_saldo = models.TextField(
        blank=True
    )

    texto_email_aniversario = models.TextField(
        blank=True
    )

    texto_sms_aniversario = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.matriz.nome