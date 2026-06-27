import uuid

from django.conf import settings
from django.db import models

from empresas.models import Matriz, Loja


class RegistroAuditoria(models.Model):

    ACAO_LOGIN = 'login'
    ACAO_LOGOUT = 'logout'
    ACAO_CRIAR = 'criar'
    ACAO_EDITAR = 'editar'
    ACAO_EXCLUIR = 'excluir'
    ACAO_IMPORTAR = 'importar'
    ACAO_DISPARAR = 'disparar'
    ACAO_ACESSAR = 'acessar'

    ACAO_CHOICES = [
        (ACAO_LOGIN, 'Login'),
        (ACAO_LOGOUT, 'Logout'),
        (ACAO_CRIAR, 'Criar'),
        (ACAO_EDITAR, 'Editar'),
        (ACAO_EXCLUIR, 'Excluir'),
        (ACAO_IMPORTAR, 'Importar'),
        (ACAO_DISPARAR, 'Disparar'),
        (ACAO_ACESSAR, 'Acessar'),
    ]

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='registros_auditoria'
    )

    matriz = models.ForeignKey(
        Matriz,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='registros_auditoria'
    )

    loja = models.ForeignKey(
        Loja,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='registros_auditoria'
    )

    acao = models.CharField(
        max_length=30,
        choices=ACAO_CHOICES,
        db_index=True
    )

    recurso = models.CharField(
        max_length=150,
        db_index=True
    )

    recurso_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )

    descricao = models.TextField(
        blank=True
    )

    ip = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    user_agent = models.TextField(
        blank=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['matriz', 'acao']),
            models.Index(fields=['matriz', 'criado_em']),
            models.Index(fields=['usuario', 'criado_em']),
            models.Index(fields=['recurso', 'recurso_id']),
        ]

    def __str__(self):
        return f'{self.get_acao_display()} - {self.recurso}'