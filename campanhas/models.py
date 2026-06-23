import uuid

from django.db import models

from clientes.models import Cliente
from empresas.models import Matriz


class CampanhaAniversarioEnvio(models.Model):

    CANAL_EMAIL = 'email'
    CANAL_WHATSAPP = 'whatsapp'
    CANAL_SMS = 'sms'

    CANAL_CHOICES = [
        (CANAL_EMAIL, 'E-mail'),
        (CANAL_WHATSAPP, 'WhatsApp'),
        (CANAL_SMS, 'SMS'),
    ]

    STATUS_PENDENTE = 'pendente'
    STATUS_ENVIADO = 'enviado'
    STATUS_ERRO = 'erro'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_ENVIADO, 'Enviado'),
        (STATUS_ERRO, 'Erro'),
    ]

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.CASCADE,
        related_name='campanhas_aniversario'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='campanhas_aniversario'
    )

    canal = models.CharField(
        max_length=20,
        choices=CANAL_CHOICES,
        db_index=True
    )

    assunto = models.CharField(
        max_length=150,
        blank=True
    )

    mensagem = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
        db_index=True
    )

    erro = models.TextField(
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    enviado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['matriz', 'canal']),
            models.Index(fields=['matriz', 'status']),
            models.Index(fields=['matriz', 'criado_em']),
            models.Index(fields=['cliente', 'canal']),
        ]

    def __str__(self):
        return f'{self.cliente.nome} - {self.get_canal_display()}'