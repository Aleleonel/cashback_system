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
    STATUS_PROCESSANDO = 'processando'
    STATUS_ENVIADO = 'enviado'
    STATUS_ERRO = 'erro'

    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PROCESSANDO, 'Processando'),
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
    

class ConfiguracaoCampanhaAniversario(models.Model):

    CANAL_EMAIL = 'email'
    CANAL_WHATSAPP = 'whatsapp'
    CANAL_SMS = 'sms'

    CANAL_CHOICES = [
        (CANAL_EMAIL, 'E-mail'),
        (CANAL_WHATSAPP, 'WhatsApp'),
        (CANAL_SMS, 'SMS'),
    ]

    matriz = models.OneToOneField(
        Matriz,
        on_delete=models.CASCADE,
        related_name='configuracao_campanha_aniversario'
    )

    ativa = models.BooleanField(default=True)

    canal_padrao = models.CharField(
        max_length=20,
        choices=CANAL_CHOICES,
        default=CANAL_EMAIL
    )

    assunto_padrao = models.CharField(
        max_length=150,
        default='Feliz aniversário! Temos um presente especial para você'
    )

    mensagem_padrao = models.TextField(
        default=(
            'Olá, {nome}! A equipe preparou uma condição especial '
            'para comemorar seu aniversário. Entre em contato e aproveite!'
        )
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Campanha de Aniversário'
        verbose_name_plural = 'Configurações de Campanhas de Aniversário'

    def __str__(self):
        return f'Campanha de aniversário - {self.matriz.nome}'
    

class TemplateCampanha(models.Model):
        

        TIPO_ANIVERSARIO = 'aniversario'
        TIPO_CASHBACK_EXPIRANDO = 'cashback_expirando'
        TIPO_BOAS_VINDAS = 'boas_vindas'
        TIPO_PERSONALIZADA = 'personalizada'

        TIPO_CHOICES = [
            (TIPO_ANIVERSARIO, 'Aniversário'),
            (TIPO_CASHBACK_EXPIRANDO, 'Cashback Expirando'),
            (TIPO_BOAS_VINDAS, 'Boas-vindas'),
            (TIPO_PERSONALIZADA, 'Personalizada'),
        ]

        CANAL_EMAIL = 'email'
        CANAL_WHATSAPP = 'whatsapp'
        CANAL_SMS = 'sms'

        CANAL_CHOICES = [
            (CANAL_EMAIL, 'E-mail'),
            (CANAL_WHATSAPP, 'WhatsApp'),
            (CANAL_SMS, 'SMS'),
        ]

        matriz = models.ForeignKey(
            Matriz,
            on_delete=models.CASCADE,
            related_name='templates_campanhas'
        )

        nome = models.CharField(max_length=100)

        tipo = models.CharField(
            max_length=30,
            choices=TIPO_CHOICES,
            default=TIPO_PERSONALIZADA,
            db_index=True
        )

        canal = models.CharField(
            max_length=20,
            choices=CANAL_CHOICES,
            default=CANAL_WHATSAPP,
            db_index=True
        )

        assunto = models.CharField(
            max_length=150,
            blank=True
        )

        mensagem = models.TextField()

        ativo = models.BooleanField(default=True)

        criado_em = models.DateTimeField(auto_now_add=True)
        atualizado_em = models.DateTimeField(auto_now=True)

        class Meta:
            ordering = ['nome']
            indexes = [
                models.Index(fields=['matriz', 'tipo']),
                models.Index(fields=['matriz', 'canal']),
                models.Index(fields=['matriz', 'ativo']),
            ]

        def __str__(self):
            return f'{self.nome} - {self.get_tipo_display()}'