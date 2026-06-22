from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from empresas.models import Loja
from clientes.models import Cliente


class ConfiguracaoCashback(models.Model):
    loja = models.OneToOneField(
        Loja,
        on_delete=models.CASCADE,
        related_name='configuracao_cashback'
    )

    percentual_cashback = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00')
    )

    dias_para_liberar = models.PositiveIntegerField(default=7)
    dias_para_expirar = models.PositiveIntegerField(default=45)

    envio_email_saldo = models.BooleanField(default=True)
    envio_aniversario_email = models.BooleanField(default=True)
    envio_aniversario_sms = models.BooleanField(default=False)

    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Configuração Cashback - {self.loja.nome}'


class LancamentoCashback(models.Model):

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('disponivel', 'Disponível'),
        ('usado', 'Usado'),
        ('expirado', 'Expirado'),
        ('cancelado', 'Cancelado'),
    ]

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
    valor_cashback = models.DecimalField(max_digits=10, decimal_places=2)

    data_compra = models.DateField(default=timezone.localdate)
    data_liberacao = models.DateField()
    data_expiracao = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )

    observacao = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_compra', '-criado_em']

    def __str__(self):
        return f'{self.cliente.nome} - R$ {self.valor_cashback}'

    def atualizar_status(self):
        hoje = timezone.localdate()

        if self.status in ['usado', 'cancelado']:
            return self.status

        if hoje > self.data_expiracao:
            self.status = 'expirado'

        elif hoje >= self.data_liberacao:
            self.status = 'disponivel'

        else:
            self.status = 'pendente'

        self.save(update_fields=['status'])
        return self.status