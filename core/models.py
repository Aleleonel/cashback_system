from django.db import models

from empresas.models import Matriz


class ConfiguracaoSistema(models.Model):

    matriz = models.OneToOneField(
        Matriz,
        on_delete=models.CASCADE,
        related_name='configuracao'
    )

    percentual_cashback = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00
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

    enviar_email_saldo = models.BooleanField(default=True)

    enviar_email_aniversario = models.BooleanField(default=True)

    enviar_sms_aniversario = models.BooleanField(default=False)

    mensagem_email_saldo = models.TextField(
        blank=True
    )

    mensagem_email_aniversario = models.TextField(
        blank=True
    )

    mensagem_sms_aniversario = models.TextField(
        blank=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f'Configuração - {self.matriz.nome}'